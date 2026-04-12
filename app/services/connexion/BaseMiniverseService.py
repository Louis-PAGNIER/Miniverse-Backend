from abc import ABC, abstractmethod

from app.schemas import MSMPPlayer
from app.services.connexion.server_status_store import server_status_store


class BaseMiniverseService(ABC):
    def __init__(self, miniverse_id: str):
        self.miniverse_id = miniverse_id

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    async def stop(self):
        pass

    @abstractmethod
    async def _get_data_from_source(self, method_name: str):
        pass

    async def _get_data_cached(self, method_name: str, refresh_cache: bool):
        if not refresh_cache:
            raw_data = await server_status_store.get(self.miniverse_id, method_name)
        else:
            raw_data = None

        has_refreshed = False
        if raw_data is None:
            raw_data = await self._get_data_from_source(method_name)
            await server_status_store.set(self.miniverse_id, method_name, raw_data)
            has_refreshed = True
        return raw_data, has_refreshed

    async def get_msmp_player_list(self, refresh_cache=False) -> list[MSMPPlayer]:
        raw_player_list, has_refreshed = await self._get_data_cached("minecraft:players", refresh_cache)
        if raw_player_list is None:
            return []

        if has_refreshed:
            seen_player_dict = (await server_status_store.get(self.miniverse_id, "miniverse:seen_players")) or {}
            seen_player_dict |= {p["id"]: p for p in raw_player_list}
            await server_status_store.set(self.miniverse_id, "miniverse:seen_players", seen_player_dict, publish=False)

        return [MSMPPlayer(**d) for d in raw_player_list]

    async def get_msmp_seen_player_list(self) -> list[MSMPPlayer]:
        seen_player_dict = (await server_status_store.get(self.miniverse_id, "miniverse:seen_players")) or {}
        return [MSMPPlayer(**p) for p in seen_player_dict.values()]