import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Miniverse
from app.services.docker_service import dockerctl, VolumeConfig


def generate_router_routes(miniverse_list: list[Miniverse]) -> dict:
    return {
        "mappings": {
            f"{m.subdomain}.{settings.DOMAIN_NAME}": f"miniverse-{m.id}:25565"
            for m in miniverse_list
        }
    }

async def update_proxy_config(db: AsyncSession) -> None:
    miniverses = await db.execute(select(Miniverse))
    miniverse_list = list(miniverses.scalars().all())

    routes_data = generate_router_routes(miniverse_list)
    routes_path = settings.DATA_PATH / "proxy" / "routes.json"
    routes_path.parent.mkdir(parents=True, exist_ok=True)

    with open(routes_path, "w") as f:
        json.dump(routes_data, f, indent=4)

    router_container = await dockerctl.get_container_by_name("miniverse-router")
    if router_container:
        await dockerctl.kill_container(router_container["Id"], signal="SIGHUP")


async def start_proxy_containers() -> None:
    host_routes_dir = settings.HOST_DATA_PATH / "proxy"

    router_container = await dockerctl.get_container_by_name("miniverse-router")

    if router_container is None:
        await dockerctl.create_container(
            image="itzg/mc-router:latest",
            name="miniverse-router",
            network_id=settings.DOCKER_NETWORK_NAME,
            volumes={str(host_routes_dir): VolumeConfig(bind="/config", mode="ro")},
            ports={"25565/tcp": 25565},
            command=[
                "--routes-config", "/config/routes.json", "--routes-config-watch", "--connection-rate-limit", "10"
            ],
            auto_remove=True,
        )
        await dockerctl.start_container("miniverse-router")


async def stop_proxy_containers() -> None:
    proxy_container = await dockerctl.get_container_by_name("miniverse-router")
    if proxy_container:
        await dockerctl.stop_container(proxy_container["Id"])
