from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.core import settings
from app.core.config import DATA_PATH
from app.core.utils import generate_random_string
from app.enums import MiniverseType, Role
from app.managers import server_status_manager
from app.models import Miniverse, MiniverseUserRole, User
from app.schemas.miniverse import MiniverseCreate
from app.services.docker_service import dockerctl, VolumeConfig

import re
import shutil
import toml

from app.services.proxy_service import update_proxy_config
from app.services.mods_service import install_mod_for_miniverse


def get_miniverse_path(proxy_id: str, *subpaths: str, from_host: bool = False) -> Path:
    if from_host:
        return Path(settings.HOST_DATA_PATH) / "miniverses" / proxy_id / Path(*subpaths)
    return DATA_PATH / "miniverses" / proxy_id / Path(*subpaths)

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
        is_on_main_proxy=miniverse.is_on_main_proxy,
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

    container = await create_miniverse_container(db_miniverse, db)
    db_miniverse.container_id = container["Id"]
    await db.commit()
    await db.refresh(db_miniverse)

    await dockerctl.start_container(container["Id"])
    await update_proxy_config(db)

    server_status_manager.add_miniverse(db_miniverse)

    return db_miniverse


async def delete_miniverse(miniverse: Miniverse, db: AsyncSession):
    server_status_manager.remove_miniverse(miniverse.id)
    if miniverse.container_id:
        # remove_container also stops the container if it's running using force=True (SIGKILL)
        logger.info(f"Deleting miniverse {miniverse.name} (ID: {miniverse.id})")
        await dockerctl.remove_container(miniverse.container_id)

    volume_base_path = get_miniverse_path(miniverse.id)
    if volume_base_path.exists() and volume_base_path.is_dir():
        shutil.rmtree(volume_base_path)
    await db.delete(miniverse)
    await db.commit()
    await update_proxy_config(db)


async def create_miniverse_container(miniverse: Miniverse, db: AsyncSession) -> dict:
    logger.info(f"Creating miniverse container for miniverse {miniverse.name}")
    container_name = "miniverse-" + miniverse.id

    volume_data_path = get_miniverse_path(miniverse.id, "data")
    volume_data_path.mkdir(parents=True, exist_ok=True)

    await init_data_path(miniverse, db)

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
            "ONLINE_MODE": "TRUE" if miniverse.is_on_main_proxy else "FALSE",
            "SERVER_PORT": "25565",
            "MANAGEMENT_SERVER_ENABLED": "TRUE",
            "MANAGEMENT_SERVER_TLS_ENABLED": "FALSE",
            "MANAGEMENT_SERVER_HOST": "0.0.0.0",
            "MANAGEMENT_SERVER_PORT": "25585",
            "MANAGEMENT_SERVER_SECRET": miniverse.management_server_secret,
        },
        tty=True,
        stdin_open=True,
    )

    return container


async def init_data_path(miniverse: Miniverse, db: AsyncSession):
    volume_data_path = get_miniverse_path(miniverse.id, "data")
    game_version = miniverse.mc_version

    # TODO: Move snapshot detection to a utility function
    is_snapshot = re.match(r"^\d{2}w\d{2}[a-z]$", game_version) is not None
    is_prerelease = re.match(r"^\d{1,2}\.\d{1,2}\.\d{1,2}-(pre|rc)\d*$", game_version) is not None
    prioritize_release = not (is_snapshot or is_prerelease)

    if not miniverse.is_on_main_proxy:
        config_path = volume_data_path / "config"
        config_path.mkdir(parents=True, exist_ok=True)

        if miniverse.type == MiniverseType.FABRIC:
            await install_mod_for_miniverse("P7dR8mSH", miniverse, db, prioritize_release=prioritize_release) # Fabric API
            await install_mod_for_miniverse("8dI2tmqs", miniverse, db, prioritize_release=prioritize_release, retry_with_latest=True) # FabricProxy-Lite
            fabric_proxy_lite_config = config_path / "FabricProxy-Lite.toml"
            with open(str(fabric_proxy_lite_config), "w") as f:
                toml.dump({"secret": settings.PROXY_SECRET}, f)
        elif miniverse.type == MiniverseType.NEO_FORGE or miniverse.type == MiniverseType.FORGE:
            await install_mod_for_miniverse("vDyrHl8l", miniverse, db, prioritize_release=prioritize_release, retry_with_latest=True) # FabricProxy-Lite
            fabric_proxy_lite_config = config_path / "pcf-common.toml"
            with open(str(fabric_proxy_lite_config), "w") as f:
                toml.dump({"modernForwarding": { "forwardingSecret": settings.PROXY_SECRET } }, f)
        else:
            logger.warning(f"Miniverse type {miniverse.type} is currently not supported for standalone miniverses.")
