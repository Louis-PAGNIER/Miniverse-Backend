from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.core import settings
from app.core.utils import generate_random_string
from app.enums import MiniverseType, Role
from app.models import Miniverse, MiniverseUserRole, User
from app.schemas.miniverse import MiniverseCreate
from app.services.docker_service import dockerctl, VolumeConfig
from app.services.mods_service import install_mod

import shutil

from app.services.proxy_service import update_proxy_config


def get_miniverse_path(proxy_id: str, *subpaths: str) -> Path:
    return Path(settings.DATA_PATH) / "miniverses" / proxy_id / Path(*subpaths)

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

    container = await create_miniverse_container(db_miniverse)
    db_miniverse.container_id = container["Id"]
    await db.commit()
    await db.refresh(db_miniverse)

    await dockerctl.start_container(container["Id"])
    await update_proxy_config(db)

    return db_miniverse


async def delete_miniverse(miniverse: Miniverse, db: AsyncSession):
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


async def create_miniverse_container(miniverse: Miniverse) -> dict:
    logger.info(f"Creating miniverse container for miniverse {miniverse.name}")
    container_name = "miniverse-" + miniverse.id

    volume_data_path = get_miniverse_path(miniverse.id, "data")
    volume_data_path.mkdir(parents=True, exist_ok=True)

    await init_data_path(miniverse)

    container = await dockerctl.create_container(
        image="itzg/minecraft-server",
        name=container_name,
        network_id=settings.DOCKER_NETWORK_NAME,
        volumes={str(volume_data_path.resolve()): VolumeConfig(bind="/data")},
        ports={"25585": 25585},
        environment={
            "EULA": "TRUE",
            "TYPE": miniverse.type.value.upper(),
            "VERSION": miniverse.mc_version,
            "MOTD": f"Welcome to {miniverse.name}!",
            "ONLINE_MODE": "true",
            "SERVER_PORT": "25565",
            "MANAGEMENT_SERVER_ENABLED": "TRUE",
            "MANAGEMENT_SERVER_HOST": "0.0.0.0",
            "MANAGEMENT_SERVER_PORT": "25585",
            "MANAGEMENT_SERVER_SECRET": generate_random_string(40),
        },
        tty=True,
        stdin_open=True,
    )

    return container


async def init_data_path(miniverse: Miniverse):
    volume_data_path = get_miniverse_path(miniverse.id, "data")
    if miniverse.type == MiniverseType.FABRIC:
        # Download Fabric API
        logger.info(f"Downloading Fabric API for miniverse {miniverse.name}")
