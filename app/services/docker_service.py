import asyncio
import docker

from app import logger
from app.core import settings
from dataclasses import dataclass
from typing import Any, Literal
from docker.errors import ImageNotFound


@dataclass
class VolumeConfig:
    bind: str
    mode: Literal["ro", "rw"] = "rw"


class AsyncNetworkController:
    def __init__(self, client: docker.DockerClient):
        self.client = client

    async def list_networks(self) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            lambda: [n.attrs for n in self.client.networks.list()]
        )

    async def create_network(self, name: str, driver: str = "bridge", **kwargs) -> dict[str, Any]:
        return await asyncio.to_thread(
            lambda: self.client.networks.create(name, driver=driver, **kwargs).attrs
        )


class AsyncDockerController:
    def __init__(self):
        self.client = docker.from_env()
        self.networks = AsyncNetworkController(self.client)

    async def list_containers(self, all: bool = True) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            lambda: [c.attrs for c in self.client.containers.list(all=all)]
        )

    async def get_stats(self, container_ids: list[str]) -> dict[str, Any]:
        def _get_stats(container_id):
            container = self.client.containers.get(container_id)
            return container_id, container.stats(stream=False)

        tasks = [asyncio.to_thread(_get_stats, cid) for cid in container_ids]
        results = await asyncio.gather(*tasks)
        return {cid: stats for cid, stats in results}

    async def create_container(
        self,
        image: str,
        *,
        name: str = None,
        command: str = None,
        detach: bool = True,
        network_id: str = None,
        volumes: dict[str, VolumeConfig] = None,
        ports: dict[str, int | list[int]] = None,
        tty: bool = False,
        stdin_open: bool = False,
        environment: dict[str, str] = None,
        auto_remove: bool = False,
        **kwargs
    ) -> dict[str, Any]:
        def _create():
            try:
                self.client.images.get(image)
            except docker.errors.ImageNotFound:
                print(f"Image {image} not found, pulling...")
                self.client.images.pull(image)

            volumes_dict = {}
            if volumes:
                for host_path, vol_cfg in volumes.items():
                    volumes_dict[host_path] = vol_cfg.__dict__

            container = self.client.containers.create(
                image,
                name=name,
                command=command,
                detach=detach,
                network=network_id,
                volumes=volumes_dict,
                ports=ports,
                tty=tty,
                stdin_open=stdin_open,
                environment=environment,
                auto_remove=auto_remove,
                **kwargs
            )
            return container.attrs

        return await asyncio.to_thread(_create)

    async def start_container(self, container_id: str):
        return await asyncio.to_thread(
            lambda: self.client.containers.get(container_id).start()
        )

    async def stop_container(self, container_id: str):
        return await asyncio.to_thread(
            lambda: self.client.containers.get(container_id).stop()
        )

    async def restart_container(self, container_id: str):
        return await asyncio.to_thread(
            lambda: self.client.containers.get(container_id).restart()
        )

    async def remove_container(self, container_id: str):
        def _remove():
            try:
                container = self.client.containers.get(container_id)
                container.remove(force=True)
            except docker.errors.NotFound:
                pass
        return await asyncio.to_thread(_remove)

    async def get_container(self, container_id: str) -> dict[str, Any]:
        def _get():
            try:
                container = self.client.containers.get(container_id)
                return container.attrs
            except docker.errors.NotFound:
                return None
        return await asyncio.to_thread(_get)

    async def get_container_by_name(self, name: str) -> dict[str, Any] | None:
        def _get():
            containers = self.client.containers.list(all=True, filters={"name": name})
            if containers:
                return containers[0].attrs
            return None
        return await asyncio.to_thread(_get)

    async def initialize(self):
        networks = await self.networks.list_networks()
        if not any(n["Name"] == settings.DOCKER_NETWORK_NAME for n in networks):
            logger.info(f"{settings.DOCKER_NETWORK_NAME} network not found, creating...")
            await self.networks.create_network(settings.DOCKER_NETWORK_NAME)

dockerctl = AsyncDockerController()

