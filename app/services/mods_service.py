from pathlib import Path

import httpx
from litestar.exceptions import ValidationException
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.enums import MiniverseType
from app.events.miniverse_event import publish_miniverse_updated_event
from app.models import Miniverse, Mod
from app.schemas import ModVersionType
from app.schemas.mods import ModrinthSearchFacets, ModrinthSearchResults, ModrinthProjectVersion, ModrinthProject, \
    ModUpdateStatus, ModUpdateInfo

MODRINTH_BASE_URL = "https://api.modrinth.com/v2"

def dumps_values(values: list[str] | str) -> str:
    if isinstance(values, str):
        values = [values]
    return str(values).replace("'", '').replace("\\", "")

def build_or_facets(key: str, values: list[str] | str) -> str:
    if isinstance(values, str):
        values = [values]
    res = []
    for v in values:
        res.append(f'"{key}:{v}"')
    return str(res)

def build_facets(facets: ModrinthSearchFacets) -> str:
    res = []
    if facets.project_type is not None:
        res.append(build_or_facets("project_type", facets.project_type.value))
    if facets.categories is not None:
        res.append(build_or_facets("categories", facets.categories))
    if facets.versions is not None:
        res.append(build_or_facets("versions", facets.versions))
    if facets.client_side is not None:
        res.append(build_or_facets("client_side", facets.client_side.value))
    if facets.server_side is not None:
        res.append(build_or_facets("server_side", facets.server_side.value))
    return dumps_values(res)


async def search_modrinth_projects(query: str, facets: ModrinthSearchFacets, limit: int, offset: int = 0) -> ModrinthSearchResults:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODRINTH_BASE_URL}/search",
                                    params={
                                        "query": query,
                                        "facets": build_facets(facets),
                                        "limit": limit,
                                        "offset": offset
                                    })
        response.raise_for_status()
        data = response.json()
        return ModrinthSearchResults.from_dict(data)


async def list_project_versions(project_id: str, loader: MiniverseType = None, mc_version: str = None) -> list[ModrinthProjectVersion]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODRINTH_BASE_URL}/project/{project_id}/version",
                                    params={
                                      "loaders": dumps_values(loader.value.lower()) if loader else None,
                                      "game_versions": dumps_values(mc_version) if mc_version else None
                                    })
        response.raise_for_status()
        data = response.json()
        return [ModrinthProjectVersion.from_dict(v) for v in data]


async def get_project_details(project_id: str) -> ModrinthProject:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODRINTH_BASE_URL}/project/{project_id}")
        response.raise_for_status()
        data = response.json()
        return ModrinthProject.from_dict(data)


async def get_version_details(version_id: str) -> ModrinthProjectVersion:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODRINTH_BASE_URL}/version/{version_id}")
        response.raise_for_status()
        data = response.json()
        return ModrinthProjectVersion.from_dict(data)


async def get_mod(mod_id: str, db: AsyncSession) -> Mod | None:
    return await db.get(Mod, mod_id)


async def download_mod_file(project: ModrinthProject, version: ModrinthProjectVersion, miniverse: Miniverse) -> str:
    from app.services.miniverse_service import get_miniverse_path
    primary_file = next((f for f in version.files if f.primary), None)
    if not primary_file:
        raise ValidationException("No primary file found for this mod version")
    extension = Path(primary_file.filename).suffix
    if extension != ".jar":
        raise ValidationException("Unsupported file type for mod installation: " + extension)

    # TODO: wrap the name to be filesystem-safe
    file_name = f"{project.slug}-{version.version_number}-{version.id}{extension}"

    mods_path = get_miniverse_path(miniverse.id, "data", "mods")
    mods_path.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient() as client:
        download_response = await client.get(primary_file.url)
    download_response.raise_for_status()

    with open(mods_path / file_name, "wb") as f:
        f.write(download_response.content)

    return file_name


async def delete_mod_file(mod: Mod) -> None:
    from app.services.miniverse_service import get_miniverse_path
    mods_path = get_miniverse_path(mod.miniverse_id,  "data", "mods")
    mod_file_path = mods_path / mod.file_name
    if mod_file_path.exists() and mod_file_path.is_file():
        mod_file_path.unlink()


async def install_mod(mod_version_id: str, miniverse: Miniverse, db: AsyncSession) -> Mod:
    version = await get_version_details(mod_version_id)
    project = await get_project_details(version.project_id)

    file_name = await download_mod_file(project, version, miniverse)
    mod = Mod(
        slug=project.slug,
        version_id=version.id,
        project_id=version.project_id,
        title=project.title,
        icon_url=project.icon_url,
        version_name=version.name,
        version_number=version.version_number,
        file_name=file_name,
        miniverse_id=miniverse.id,
    )

    db.add(mod)
    await db.commit()
    await db.refresh(mod)

    logger.info(f"Mod {mod.slug} installed")
    publish_miniverse_updated_event(miniverse.id)

    return mod

async def update_mod(mod: Mod, new_version_id: str, db: AsyncSession) -> Mod:
    version = await get_version_details(new_version_id)
    project = await get_project_details(version.project_id)

    await delete_mod_file(mod)
    file_name = await download_mod_file(project, version, mod.miniverse)

    mod.version_id = version.id
    mod.project_id = version.project_id
    mod.title = project.title
    mod.icon_url = project.icon_url
    mod.version_name = version.name
    mod.version_number = version.version_number
    mod.file_name = file_name

    await db.commit()
    await db.refresh(mod)

    logger.info(f"Mod {mod.slug} updated")
    publish_miniverse_updated_event(mod.miniverse_id)

    return mod


async def automatic_mod_install(
        mod_id: str,
        miniverse: Miniverse,
        db: AsyncSession,
        *,
        game_version: str | None = None,
        prioritize_release: bool = True,
        retry_with_latest: bool = False
) -> Mod:
    if game_version is None:
        game_version = miniverse.mc_version
    versions = await list_project_versions(mod_id, loader=miniverse.type, mc_version=game_version)
    if not versions:
        if retry_with_latest:
            versions = await list_project_versions(mod_id, loader=miniverse.type)
        if not versions:
            raise ValidationException(f"No compatible versions found for mod {mod_id} with loader {miniverse.type} and game version {game_version}")
        logger.warning(f"No direct compatible versions found for mod {mod_id} with loader {miniverse.type} and game version {game_version}, falling back to latest available version")
    if prioritize_release:
        versions = [v for v in versions if v.version_type == ModVersionType.RELEASE] or versions
    latest_version = sorted(versions, key=lambda v: v.date_published, reverse=True)[0]

    return await install_mod(latest_version.id, miniverse, db)


async def uninstall_mod(mod: Mod, db: AsyncSession) -> None:
    miniverse_id = mod.miniverse_id

    await delete_mod_file(mod)
    await db.delete(mod)
    await db.commit()

    logger.info(f"Mod {mod.slug} uninstalled")
    publish_miniverse_updated_event(miniverse_id)


async def list_possible_mod_updates(miniverse: Miniverse, game_version: str | None = None) -> dict[str, ModUpdateInfo]:
    mods = miniverse.mods
    updates = {}
    if game_version is None:
        game_version = miniverse.mc_version
    for mod in mods:
        try:
            versions = await list_project_versions(mod.project_id, loader=miniverse.type, mc_version=game_version)
            if not versions:
                versions = await list_project_versions(mod.project_id, loader=miniverse.type)
            if not versions:
                logger.warning(f"No versions found for mod {mod.project_id} when checking for updates")
                updates[mod.id] = ModUpdateInfo(ModUpdateStatus.ERROR, [], [])
                continue
            versions = sorted(versions, key=lambda v: v.date_published, reverse=True)
            for version in versions:
                if game_version in version.game_versions or version.id == mod.version_id:
                    if version.id == mod.version_id:
                        updates[mod.id] = ModUpdateInfo(ModUpdateStatus.ALREADY_UP_TO_DATE, [version.id], [version.game_versions])
                    else:
                        updates[mod.id] = ModUpdateInfo(ModUpdateStatus.UPDATE_AVAILABLE, [version.id], [version.game_versions])
                    break
            else:
                updates[mod.id] = ModUpdateInfo(ModUpdateStatus.NO_COMPATIBLE_VERSIONS, [v.id for v in versions], [v.game_versions for v in versions])
        except Exception as e:
            logger.error(f"Error checking for updates for mod {mod.id}: {e}")
            updates[mod.id] = ModUpdateInfo(ModUpdateStatus.ERROR, [], [])
    return updates