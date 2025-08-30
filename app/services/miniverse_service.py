from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.core import settings
from app.models import Miniverse
from app.schemas.miniverse import MiniverseCreate
from app.services.docker_service import dockerctl, VolumeConfig
from app.services.proxy_service import update_proxy_config

import shutil

MINIVERSES_VOLUME_PATH = Path(settings.DATA_PATH) / "miniverses"

async def get_miniverses(db: AsyncSession) -> list[Miniverse]:
    result = await db.execute(select(Miniverse))
    return list(result.scalars().all())

async def get_miniverse(miniverse_id: str, db: AsyncSession) -> Miniverse | None:
    result = await db.execute(select(Miniverse).where(Miniverse.id == miniverse_id))
    return result.scalars().first()

async def create_miniverse(miniverse: MiniverseCreate, db: AsyncSession) -> Miniverse:
    db_miniverse = Miniverse(
        name=miniverse.name,
        type=miniverse.type,
        description=miniverse.description,
        mc_version=miniverse.mc_version,
        subdomain=miniverse.subdomain,
        proxy_id=miniverse.proxy_id,
        # TODO: Check if the user has permission to use the selected proxy
    )
    db.add(db_miniverse)
    await db.commit()
    await db.refresh(db_miniverse)
    container = await create_miniverse_container(db_miniverse, db)
    db_miniverse.container_id = container["Id"]
    await db.commit()
    await db.refresh(db_miniverse)
    await dockerctl.start_container(container["Id"])
    await update_proxy_config(db_miniverse.proxy, db, restart=True)

    return db_miniverse


async def delete_miniverse(miniverse: Miniverse, db: AsyncSession):
    proxy = miniverse.proxy
    if miniverse.container_id:
        # remove_container also stops the container if it's running using force=True (SIGKILL)
        logger.info(f"Deleting miniverse {miniverse.name} (ID: {miniverse.id})")
        await dockerctl.remove_container(miniverse.container_id)

    volume_base_path = MINIVERSES_VOLUME_PATH / miniverse.id
    if volume_base_path.exists() and volume_base_path.is_dir():
        shutil.rmtree(volume_base_path)
    await db.delete(miniverse)
    await db.commit()
    await update_proxy_config(proxy, db, restart=True)


async def create_miniverse_container(miniverse: Miniverse, db: AsyncSession) -> dict:
    logger.info(f"Creating miniverse container for miniverse {miniverse.name}")
    container_name = "miniverse-" + miniverse.id

    volume_base_path = MINIVERSES_VOLUME_PATH / miniverse.id
    volume_base_path.mkdir(parents=True)

    volume_data_path = volume_base_path / "data"
    volume_data_path.mkdir()

    container = await dockerctl.create_container(
        image="itzg/minecraft-server",
        name=container_name,
        network_id=settings.DOCKER_NETWORK_NAME,
        volumes={str(volume_data_path.resolve()): VolumeConfig(bind="/data")},
        ports={"25565/tcp": None},
        environment={
            "EULA": "TRUE",
            "TYPE": miniverse.type.value.upper(),
            "VERSION": miniverse.mc_version,
            "MOTD": f"Welcome to {miniverse.name}!",
            "ONLINE_MODE": "false",
            "SERVER_PORT": "25565",
        },
        tty=True,
        stdin_open=True,
    )

    return container