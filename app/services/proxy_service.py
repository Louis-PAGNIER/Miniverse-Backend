from uuid import uuid4

import toml

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import logger
from app.core import settings
from app.models import Proxy
from app.schemas.proxy import ProxyCreate
from app.services.configs_generator import generate_velocity_config
from app.services.docker_service import dockerctl, VolumeConfig

PROXIES_VOLUME_PATH = Path(settings.DATA_PATH) / "proxies"

async def get_proxies(db: AsyncSession) -> list[Proxy]:
    result = await db.execute(select(Proxy))
    return list(result.scalars().all())


async def create_proxy(proxy: ProxyCreate, db: AsyncSession) -> Proxy:
    db_proxy = Proxy(
        name=proxy.name,
        type=proxy.type,
        port=proxy.port,
        description=proxy.description,
    )
    db.add(db_proxy)
    await db.commit()
    await db.refresh(db_proxy)
    await create_proxy_container(db_proxy, db)
    return db_proxy


async def update_velocity_config(proxy: Proxy, db: AsyncSession, restart: bool = True):
    volume_config_path = PROXIES_VOLUME_PATH / proxy.id / "config" / "velocity.toml"
    config = await generate_velocity_config(proxy, db)
    with open(volume_config_path, "w") as f:
        toml.dump(config, f)
    if restart:
        await dockerctl.restart_container(proxy.container_id)


async def create_proxy_container(proxy: Proxy, db: AsyncSession) -> None:
    logger.info(f"Creating proxy container for proxy {proxy.name} on port {proxy.port}")
    container_name = "miniverse_proxy_" + proxy.name

    volume_base_path = PROXIES_VOLUME_PATH / proxy.id
    volume_base_path.mkdir(parents=True)

    volume_config_path = volume_base_path / "config"
    volume_config_path.mkdir()
    forwarding_secret_path = volume_config_path / "forwarding.secret"
    with open(forwarding_secret_path, "w") as f:
        f.write(str(uuid4()))

    await update_velocity_config(proxy, db, restart=False)






    container = await dockerctl.create_container(
        image="itzg/mc-proxy",
        name=container_name,
        network_id=settings.DOCKER_NETWORK_NAME,
        volumes={
            str(volume_config_path.resolve()): VolumeConfig(bind="/config", mode="ro"),
        },
        ports={'25565/tcp': proxy.port},
        environment={
            "TYPE": proxy.type.value.upper(),

        }
    )

    print(container)

