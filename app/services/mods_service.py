from pathlib import Path

import httpx
from litestar.exceptions import ValidationException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Miniverse, Mod
from app.schemas.mods import ModrinthSearchFacets, ModrinthSearchResults, ModrinthProjectVersion, ModrinthProject

MODRINTH_BASE_URL = "https://api.modrinth.com/v2"

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
    return str(res).replace("'", "").replace("\\", "")


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


async def list_project_versions(project_id: str) -> list[ModrinthProjectVersion]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODRINTH_BASE_URL}/project/{project_id}/version")
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


async def install_mod(mod_version_id: str, miniverse: Miniverse, db: AsyncSession) -> Mod:
    from app.services.miniverse_service import get_miniverse_path
    async with httpx.AsyncClient() as client:
        version = await get_version_details(mod_version_id)
        project = await get_project_details(version.project_id)

        primary_file = next((f for f in version.files if f.primary), None)
        if not primary_file:
            raise ValidationException("No primary file found for this mod version")
        extension = Path(primary_file.filename).suffix
        if extension != ".jar":
            raise ValidationException("Unsupported file type for mod installation: " + extension)

        # TODO: wrap the name to be filesystem-safe
        file_name = f"{project.slug}-{version.version_number}-{version.id}{extension}"

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

        mods_path = get_miniverse_path(miniverse.id,  "data", "mods")
        mods_path.mkdir(parents=True, exist_ok=True)

        download_response = await client.get(primary_file.url)
        download_response.raise_for_status()

        with open(mods_path / file_name, "wb") as f:
            f.write(download_response.content)

        return mod


async def uninstall_mod(mod: Mod, miniverse: Miniverse, db: AsyncSession) -> None:
    from app.services.miniverse_service import get_miniverse_path
    mods_path = get_miniverse_path(miniverse.id,  "data", "mods")
    mod_file_path = mods_path / mod.file_name
    if mod_file_path.exists() and mod_file_path.is_file():
        mod_file_path.unlink()

    await db.delete(mod)
    await db.commit()