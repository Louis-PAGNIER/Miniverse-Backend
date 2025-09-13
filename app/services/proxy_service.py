from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Miniverse
from app.core.config import settings

import yaml

from app.services.docker_service import dockerctl, VolumeConfig


def generate_main_proxy_config(miniverse_list: list[Miniverse]) -> dict:
    return {
        "config": {
            "bind": "0.0.0.0:25565",
            "lite": {
                "enabled": True,
                "routes": [
                    {
                        "host": f"{miniverse.subdomain}.miniverse.fr",
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
            "onlineMode": False,
            "servers": {
                miniverse.id: f"miniverse-{miniverse.id}:25565" for miniverse in miniverse_list
            },
            "try": [miniverse.id for miniverse in miniverse_list],
            "status": {
                "motd": "§bA Miniverse Server",
                "showMaxPlayers": 1000,
            },
            "acceptTransfers": True,
        },
        "api": {
            "enabled": True,
            "bind": "0.0.0.0:8080"
        }
    }


async def update_proxy_config(db: AsyncSession) -> None:
    miniverses = await db.execute(select(Miniverse))
    miniverse_list = list(miniverses.scalars().all())
    data_path = Path(settings.DATA_PATH)

    main_proxy_config = generate_main_proxy_config([miniverse for miniverse in miniverse_list if miniverse.is_on_main_proxy])
    main_proxy_config_path = data_path / "proxy" / "configs" / "config-main.yml"

    classic_proxy_config = generate_classic_proxy_config([miniverse for miniverse in miniverse_list if not miniverse.is_on_main_proxy])
    classic_proxy_config_path = data_path / "proxy" / "configs" /"config-classic.yml"

    main_proxy_config_path.parent.mkdir(parents=True, exist_ok=True)

    with main_proxy_config_path.open("w") as f:
        yaml.dump(main_proxy_config, f)
    with classic_proxy_config_path.open("w") as f:
        yaml.dump(classic_proxy_config, f)


async def start_proxy_containers() -> None:
    data_path = Path(settings.DATA_PATH)
    main_proxy_config_path = data_path / "proxy" / "configs" /"config-main.yml"
    classic_proxy_config_path = data_path / "proxy" / "configs" /"config-classic.yml"

    main_container = await dockerctl.get_container_by_name("miniverse-gate-main")
    if main_container is None:
        main_container = await dockerctl.create_container(
            image="ghcr.io/minekube/gate:latest",
            name="miniverse-gate-main",
            network_id=settings.DOCKER_NETWORK_NAME,
            volumes={str(main_proxy_config_path.parent.resolve()): VolumeConfig(bind="/configs")},
            ports={"25565/tcp": 25565},
            entrypoint="/gate",
            command=["--config", "/configs/config-main.yml"],
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
            volumes={str(classic_proxy_config_path.parent.resolve()): VolumeConfig(bind="/configs")},
            ports={"8080/tcp": 8080},
            entrypoint="/gate",
            command=["--config", "/configs/config-classic.yml"]
        )
        await dockerctl.start_container(classic_container["Id"])
    else:
        await dockerctl.restart_container(classic_container["Id"])

