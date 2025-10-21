import shutil
from pathlib import Path

import toml
from litestar.exceptions import ValidationException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.core import settings
from app.core.utils import generate_random_string
from app.enums import MiniverseType, Role
from app.events.miniverse_events import publish_miniverse_deleted_event, publish_miniverse_created_event, \
    publish_miniverse_updated_event
from app.managers import server_status_manager
from app.models import Miniverse, MiniverseUserRole, User
from app.schemas import ModUpdateStatus
from app.schemas.miniverse import MiniverseCreate
from app.services.docker_service import dockerctl, VolumeConfig
from app.services.minecraft_service import is_release, compare_versions
from app.services.mods_service import automatic_mod_install, list_possible_mod_updates, update_mod
from app.services.proxy_service import update_proxy_config


def get_miniverse_path(proxy_id: str, *subpaths: str, from_host: bool = False) -> Path:
    if from_host:
        return settings.HOST_DATA_PATH / "miniverses" / proxy_id / Path(*subpaths)
    return settings.DATA_PATH / "miniverses" / proxy_id / Path(*subpaths)

async def get_miniverses(db: AsyncSession) -> list[Miniverse]:
    result = await db.execute(select(Miniverse))
    return list(result.scalars().all())

async def get_miniverse(miniverse_id: str, db: AsyncSession) -> Miniverse | None:
    result = await db.execute(select(Miniverse).where(Miniverse.id == miniverse_id))
    return result.scalars().first()

async def create_miniverse(miniverse: MiniverseCreate, creator: User, db: AsyncSession) -> Miniverse:
    db_miniverse = Miniverse(
        name=miniverse.name,
        type=miniverse.type,
        description=miniverse.description,
        mc_version=miniverse.mc_version,
        subdomain=miniverse.subdomain,
        is_on_lite_proxy=miniverse.is_on_lite_proxy,
        management_server_secret=generate_random_string(40),
    )
    db.add(db_miniverse)
    await db.commit()
    await db.refresh(db_miniverse)

    # Assign the creator as ADMIN of the miniverse
    user_role = MiniverseUserRole(
        user_id=creator.id,
        miniverse_id=db_miniverse.id,
        role=Role.ADMIN,
    )
    db.add(user_role)
    await db.commit()
    await db.refresh(user_role)

    volume_data_path = get_miniverse_path(db_miniverse.id, "data")
    volume_data_path.mkdir(parents=True, exist_ok=True)
    await init_data_path(db_miniverse, db)

    await start_miniverse(db_miniverse, db)
    await update_proxy_config(db)

    publish_miniverse_created_event(db_miniverse.id)

    return db_miniverse


async def delete_miniverse(miniverse: Miniverse, db: AsyncSession):
    miniverse_id = miniverse.id
    server_status_manager.remove_miniverse(miniverse_id)
    if miniverse.container_id:
        # remove_container also stops the container if it's running using force=True (SIGKILL)
        logger.info(f"Deleting miniverse {miniverse.name} (ID: {miniverse_id})")
        await dockerctl.remove_container(miniverse.container_id)

    volume_base_path = get_miniverse_path(miniverse_id)
    if volume_base_path.exists() and volume_base_path.is_dir():
        shutil.rmtree(volume_base_path)

    await db.delete(miniverse)
    await db.commit()
    await update_proxy_config(db)

    publish_miniverse_deleted_event(miniverse_id)


async def create_miniverse_container(miniverse: Miniverse, db: AsyncSession) -> dict:
    logger.info(f"Creating miniverse container for miniverse {miniverse.name}")
    container_name = "miniverse-" + miniverse.id

    host_volume_data_path = get_miniverse_path(miniverse.id, "data", from_host=True)

    container = await dockerctl.create_container(
        image="itzg/minecraft-server",
        name=container_name,
        network_id=settings.DOCKER_NETWORK_NAME,
        volumes={str(host_volume_data_path): VolumeConfig(bind="/data")},
        environment={
            "EULA": "TRUE",
            "TYPE": miniverse.type.value.upper(),
            "VERSION": miniverse.mc_version,
            "MOTD": f"Welcome to {miniverse.name}!",
            "ONLINE_MODE": "TRUE" if miniverse.is_on_lite_proxy else "FALSE",
            "SERVER_PORT": "25565",
            "MANAGEMENT_SERVER_ENABLED": "TRUE",
            "MANAGEMENT_SERVER_TLS_ENABLED": "FALSE",
            "MANAGEMENT_SERVER_HOST": "0.0.0.0",
            "MANAGEMENT_SERVER_PORT": "25585",
            "MANAGEMENT_SERVER_SECRET": miniverse.management_server_secret,
        },
        tty=True,
        stdin_open=True,
        auto_remove=True,
    )

    miniverse.container_id = container["Id"]
    await db.commit()
    await db.refresh(miniverse)

    return container


async def init_data_path(miniverse: Miniverse, db: AsyncSession):
    volume_data_path = get_miniverse_path(miniverse.id, "data")
    game_version = miniverse.mc_version

    prioritize_release = is_release(game_version)

    if not miniverse.is_on_lite_proxy:
        config_path = volume_data_path / "config"
        config_path.mkdir(parents=True, exist_ok=True)

        if miniverse.type == MiniverseType.FABRIC:
            await automatic_mod_install("P7dR8mSH", miniverse, db, prioritize_release=prioritize_release) # Fabric API
            await automatic_mod_install("8dI2tmqs", miniverse, db, prioritize_release=prioritize_release, retry_with_latest=True) # FabricProxy-Lite
            fabric_proxy_lite_config = config_path / "FabricProxy-Lite.toml"
            with open(str(fabric_proxy_lite_config), "w") as f:
                toml.dump({"secret": settings.PROXY_SECRET}, f)
        elif miniverse.type == MiniverseType.NEO_FORGE or miniverse.type == MiniverseType.FORGE:
            await automatic_mod_install("vDyrHl8l", miniverse, db, prioritize_release=prioritize_release, retry_with_latest=True) # FabricProxy-Lite
            fabric_proxy_lite_config = config_path / "pcf-common.toml"
            with open(str(fabric_proxy_lite_config), "w") as f:
                toml.dump({"modernForwarding": { "forwardingSecret": settings.PROXY_SECRET } }, f)
        else:
            logger.warning(f"Miniverse type {miniverse.type} is currently not supported for standalone miniverses.")


async def start_miniverse(miniverse: Miniverse, db: AsyncSession) -> dict:
    miniverse.started = True
    await db.commit()
    await db.refresh(miniverse)

    server_status_manager.add_miniverse(miniverse)

    existing_container = await dockerctl.get_container_by_name("miniverse-" + miniverse.id)
    if existing_container:
        miniverse.container_id = existing_container["Id"]
        await db.commit()
        await db.refresh(miniverse)
        await dockerctl.start_container(existing_container["Id"])
        return existing_container

    container = await create_miniverse_container(miniverse, db)
    await dockerctl.start_container(container["Id"])

    publish_miniverse_updated_event(miniverse.id)

    return container


async def stop_miniverse_container(miniverse: Miniverse) -> None:
    container_id = miniverse.container_id
    if container_id is None:
        container = await dockerctl.get_container_by_name("miniverse-" + miniverse.id)
        if container:
            container_id = container["Id"]
    if miniverse.container_id:
        await dockerctl.stop_container(container_id)


async def stop_miniverse(miniverse: Miniverse, db: AsyncSession) -> None:
    await stop_miniverse_container(miniverse)

    miniverse.started = False
    miniverse.container_id = None
    await db.commit()
    await db.refresh(miniverse)

    server_status_manager.remove_miniverse(miniverse)

    publish_miniverse_updated_event(miniverse.id)


async def restart_miniverse(miniverse: Miniverse, db: AsyncSession) -> dict:
    await stop_miniverse(miniverse, db)
    return await start_miniverse(miniverse, db)


async def update_miniverse(miniverse: Miniverse, new_mc_version: str, db: AsyncSession, force_update: bool = False) -> Miniverse:
    if miniverse.mc_version == new_mc_version:
        raise ValidationException("The new Minecraft version is the same as the current one.")

    version_comparison = await compare_versions(miniverse.mc_version, new_mc_version)
    if version_comparison is None:
        raise ValidationException("The specified Minecraft versions is invalid.")
    if version_comparison > 0:
        raise ValidationException("Downgrading Minecraft versions is not supported.")

    if miniverse.type in [MiniverseType.FORGE, MiniverseType.NEO_FORGE, MiniverseType.FABRIC]:
        # TODO: Update mods to compatible versions
        possible_mod_updates = await list_possible_mod_updates(miniverse, new_mc_version)

        safe_update = True
        for mod_id, update_info in possible_mod_updates.items():
            if update_info.update_status in [ModUpdateStatus.ERROR, ModUpdateStatus.NO_COMPATIBLE_VERSIONS]:
                safe_update = False
                logger.warning(f"Mod {mod_id} cannot be updated to be compatible with Minecraft {new_mc_version}: {update_info.update_status}")

        if not safe_update or force_update:
            raise ValidationException("One or more mods cannot be updated to be compatible with the specified Minecraft version.")

        for mod in miniverse.mods:
            update_info = possible_mod_updates[mod.id]
            if update_info.update_status == ModUpdateStatus.UPDATE_AVAILABLE:
                new_version_id = update_info.new_versions_ids[0]
                await update_mod(mod, new_version_id, db)

    await stop_miniverse(miniverse, db)

    miniverse.mc_version = new_mc_version
    await db.commit()
    await db.refresh(miniverse)

    # TODO: Delete previous jar files

    await start_miniverse(miniverse, db)

    return miniverse