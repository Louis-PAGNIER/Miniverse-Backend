import asyncio
import json

from litestar.stores.redis import RedisStore

from app import logger
from app.core import root_store
from app.enums.event_type import EventType
from app.events.miniverse_event import publish_miniverse_control_event
from app.schemas import MSMPOperator, MSMPPlayerBan, MSMPPlayer
from app.services.rpc_service import RpcService


class ServerStatusStore:
    def __init__(self, redis_store: RedisStore):
        self.redis_store = redis_store

    async def set(self, miniverse_id: str, method_name: str, value: dict | list | None, publish=True) -> None:
        key = f"{miniverse_id}.{method_name}"
        old_json_value = await self.redis_store.get(key)

        if value is not None:
            json_value = json.dumps(value)
        else:
            json_value = None

        if old_json_value != json_value:
            if json_value is not None:
                await self.redis_store.set(key, json_value)
            else:
                await self.redis_store.delete(key)
            if publish:
                publish_miniverse_control_event(miniverse_id, EventType(method_name), value)

    async def get(self, miniverse_id: str, method_id: str) -> dict | list | None:
        str_data = await self.redis_store.get(f"{miniverse_id}.{method_id}")
        if str_data is None:
            return None
        return json.loads(str_data)

    async def delete_miniverse_cache(self, miniverse_id: str):
        async for r in self.redis_store._redis.scan_iter(f"{miniverse_id}.*"):
            await self.redis_store.delete(r)


server_status_store = ServerStatusStore(root_store.with_namespace("server-status"))


class WebSocketMiniverseService:
    def __init__(self, miniverse_id: str, url: str, secret: str):
        self.miniverse_id = miniverse_id
        self.rpc: RpcService = RpcService(url, secret)
        self.task = None

    def start(self):
        if self.task is None:
            self.task: asyncio.Task = asyncio.create_task(self.rpc.async_connect_loop(on_connect=self.on_connect))
        else:
            logger.warn(f"WebSocket miniverse {self.miniverse_id} already started")

    async def stop(self):
        await self.get_msmp_player_list(
            refresh_cache=True)  # Refresh cache before stopping websocket (in case of server crash)
        if self.task is not None:
            self.task.cancel()
        else:
            logger.warn(f"WebSocket miniverse {self.miniverse_id} already stopped")
        self.task = None

    async def on_connect(self):
        self._add_handlers()

        coro_list = [
            self.get_msmp_player_list(refresh_cache=True),
            self.get_msmp_operator_list(refresh_cache=True),
            self.get_msmp_banned_player_list(refresh_cache=True),
        ]
        await asyncio.gather(*coro_list)

    def _add_handlers(self) -> None:
        self.rpc.async_add_handler("minecraft:notification/players/joined",
                                   callback=self._handle_msmp_player_list)
        self.rpc.async_add_handler("minecraft:notification/players/left",
                                   callback=self._handle_msmp_player_list)

        self.rpc.async_add_handler("minecraft:notification/operators/added",
                                   callback=self._handle_msmp_operator_list)
        self.rpc.async_add_handler("minecraft:notification/operators/removed",
                                   callback=self._handle_msmp_operator_list)

        self.rpc.async_add_handler("minecraft:notification/bans/added",
                                   callback=self._handle_msmp_banned_player_list)
        self.rpc.async_add_handler("minecraft:notification/bans/removed",
                                   callback=self._handle_msmp_banned_player_list)

        self.rpc.async_add_handler("minecraft:notification/server/saving",
                                   callback=self._handle_server_saving)

        self.rpc.async_add_handler("minecraft:notification/server/saved",
                                   callback=self._handle_server_saved)

        self.rpc.async_add_handler("minecraft:notification/server/started",
                                   callback=self._handle_server_started)

        self.rpc.async_add_handler("minecraft:notification/server/stopping",
                                   callback=self._handle_server_stopping)

    async def _handle_msmp_player_list(self, _):
        await self.get_msmp_player_list(refresh_cache=True)

    async def _handle_msmp_operator_list(self, _):
        await self.get_msmp_operator_list(refresh_cache=True)

    async def _handle_msmp_banned_player_list(self, _):
        await self.get_msmp_banned_player_list(refresh_cache=True)

    def _handle_server_saving(self):
        logger.info(f"Server save started for miniverse {self.miniverse_id}")

    def _handle_server_saved(self):
        logger.info(f"Server save completed for miniverse {self.miniverse_id}")

    def _handle_server_started(self):
        logger.info(f"Miniverse {self.miniverse_id} started")

    def _handle_server_stopping(self):
        logger.info(f"Miniverse {self.miniverse_id} is stopping...")

    async def _get_data_cached(self, method_name: str, refresh_cache: bool):
        if not refresh_cache:
            raw_data = await server_status_store.get(self.miniverse_id, method_name)
        else:
            raw_data = None
        has_refreshed = False
        if raw_data is None:
            raw_data = await self.rpc.async_call_rpc(method_name)
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

    async def get_msmp_operator_list(self, refresh_cache=False) -> list[MSMPOperator]:
        operators, _ = await self._get_data_cached("minecraft:operators", refresh_cache)
        if operators is None:
            return []
        return [MSMPOperator(**d) for d in operators]

    async def get_msmp_banned_player_list(self, refresh_cache=False) -> list[MSMPPlayerBan]:
        bans, _ = await self._get_data_cached("minecraft:bans", refresh_cache)
        if bans is None:
            return []
        return [MSMPPlayerBan(**d) for d in bans]

    async def set_player_operator(self, player_id: str, set_operator: bool) -> bool:
        if set_operator:
            op = MSMPOperator(permissionLevel=4, bypassesPlayerLimit=True, player=MSMPPlayer(id=player_id, name=""))
            result = await self.rpc.async_call_rpc("minecraft:operators/add", [op.model_dump()])
        else:
            player = MSMPPlayer(id=player_id, name="")
            result = await self.rpc.async_call_rpc("minecraft:operators/remove", [player.model_dump()])
        return result is not None

    async def kick_player(self, player_id: str, reason: str) -> bool:
        data = {
            'player': {'id': player_id},
            'message': {'literal': reason}
        }
        result = (await self.rpc.async_call_rpc("minecraft:players/kick", [data]))
        return result is not None

    async def ban_player(self, player_id: str, reason: str) -> bool:
        data = {
            'player': {'id': player_id},
            'reason': reason  #
        }
        result = (await self.rpc.async_call_rpc("minecraft:bans/add", [data]))
        return result is not None

    async def unban_player(self, player_id: str) -> bool:
        data = {'id': player_id}
        result = (await self.rpc.async_call_rpc("minecraft:bans/remove", [data]))
        return result is not None
