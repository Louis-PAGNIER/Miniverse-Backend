from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import write_yaml_safe
from app.models import Miniverse
from app.services.docker_service import dockerctl, VolumeConfig


def generate_main_proxy_config(miniverse_list: list[Miniverse]) -> dict:
    return {
        "config": {
            "bind": "0.0.0.0:25565",
            "lite": {
                "enabled": True,
                "routes": [
                    {
                        "host": f"{miniverse.subdomain}.{settings.DOMAIN_NAME}",  # TODO create env vars for domain name
                        "backend": f"miniverse-{miniverse.id}:25565",
                        "cachePingTTL": "-1s",
                        "fallback": {
                            "motd": f"§c{miniverse.name} server is offline",
                            "version": {
                                "name": "§cTry again later!",
                                "protocol": -1
                            }
                        }
                    }
                for miniverse in miniverse_list] + [
                    {
                        "host": "*",
                        "backend": "miniverse-gate-classic:25565",
                        "cachePingTTL": "-1s",
                        "fallback": {
                            "motd": "§cThe Gate classic proxy is offline",
                            "version": {
                                "name": "§cContact an administrator",
                                "protocol": -1
                            }
                        }
                    }
                ]
            }
        }
    }


def generate_classic_proxy_config(miniverse_list: list[Miniverse]) -> dict:
    return {
        "config": {
            "bind": "0.0.0.0:25565",
            "onlineMode": True,
            "servers": {
                miniverse.id: f"miniverse-{miniverse.id}:25565" for miniverse in miniverse_list
            },
            "try": [miniverse.id for miniverse in miniverse_list],
            "forcedHosts": {
                f"{miniverse.subdomain}.{settings.DOMAIN_NAME}": [miniverse.id] for miniverse in miniverse_list
            },
            "forwarding": {
                "mode": "velocity",
                "velocitySecret": settings.PROXY_SECRET,
            },
            "status": {
                "motd": "§bA Miniverse Server",
                "showMaxPlayers": 1000,
            },
            "acceptTransfers": True,
        },
        # "api": {
        #     "enabled": True, # Can be enabled to control this service
        #     "bind": "0.0.0.0:8080"
        # }
    }


async def update_proxy_config(db: AsyncSession) -> None:
    miniverses = await db.execute(select(Miniverse))
    miniverse_list = list(miniverses.scalars().all())

    main_proxy_config = generate_main_proxy_config([miniverse for miniverse in miniverse_list if miniverse.is_on_lite_proxy])
    main_proxy_config_path = settings.DATA_PATH / "proxy" / "configs" / "config-main.yml"

    classic_proxy_config = generate_classic_proxy_config([miniverse for miniverse in miniverse_list if not miniverse.is_on_lite_proxy])
    classic_proxy_config_path = settings.DATA_PATH / "proxy" / "configs" /"config-classic.yml"

    main_proxy_config_path.parent.mkdir(parents=True, exist_ok=True)

    write_yaml_safe(main_proxy_config, main_proxy_config_path)
    write_yaml_safe(classic_proxy_config, classic_proxy_config_path)


async def start_proxy_containers() -> None:
    main_proxy_config_path = settings.HOST_DATA_PATH / "proxy" / "configs" /"config-main.yml"
    classic_proxy_config_path = settings.HOST_DATA_PATH / "proxy" / "configs" /"config-classic.yml"

    main_container = await dockerctl.get_container_by_name("miniverse-gate-main")
    if main_container is None:
        main_container = await dockerctl.create_container(
            image="ghcr.io/minekube/gate:latest",
            name="miniverse-gate-main",
            network_id=settings.DOCKER_NETWORK_NAME,
            volumes={str(main_proxy_config_path.parent): VolumeConfig(bind="/configs")},
            ports={"25565/tcp": 25565},
            entrypoint="/gate",
            command=["--config", "/configs/config-main.yml"],
            auto_remove=True,
        )
        await dockerctl.start_container(main_container["Id"])
    else:
        await dockerctl.restart_container(main_container["Id"])

    classic_container = await dockerctl.get_container_by_name("miniverse-gate-classic")
    if classic_container is None:
        classic_container = await dockerctl.create_container(
            image="ghcr.io/minekube/gate:latest",
            name="miniverse-gate-classic",
            network_id=settings.DOCKER_NETWORK_NAME,
            volumes={str(classic_proxy_config_path.parent): VolumeConfig(bind="/configs")},
            # ports={"8080/tcp": 8080}, # Can be enabled to control this service
            entrypoint="/gate",
            command=["--config", "/configs/config-classic.yml"],
            auto_remove=True,
        )
        await dockerctl.start_container(classic_container["Id"])
    else:
        await dockerctl.restart_container(classic_container["Id"])


async def stop_proxy_containers() -> None:
    main_container = await dockerctl.get_container_by_name("miniverse-gate-main")
    if main_container:
        await dockerctl.stop_container(main_container["Id"])

    classic_container = await dockerctl.get_container_by_name("miniverse-gate-classic")
    if classic_container:
        await dockerctl.stop_container(classic_container["Id"])

