import asyncio
import time

miniverses_status_cache: dict[str, str] = {}
proxies_status_cache: dict[str, str] = {}

async def refresh_docker_status():
    # TODO: implement actual logic to refresh the status of miniverses and proxies
    while True:
        miniverses_status_cache["container_1"] = f"running @ {time.time()}"
        proxies_status_cache["container_2"] = f"stopped @ {time.time()}"
        await asyncio.sleep(5)


def get_miniverse_status(miniverse_id: str) -> str:
    # TODO; implement actual logic to retrieve the status of a miniverse
    return miniverses_status_cache.get(miniverse_id, "unknown")

def get_proxy_status(proxy_id: str) -> str:
    # TODO; implement actual logic to retrieve the status of a proxy
    return proxies_status_cache.get(proxy_id, "unknown")
