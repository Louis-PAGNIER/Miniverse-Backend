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

    @staticmethod
    def _publish_event(miniverse_id: str, method_id: str, value: dict | list):
        match method_id:
            case "bans":
                return publish_miniverse_control_event(miniverse_id, EventType.PLAYER_BAN, value)
            case _:  # Should work most of the time
                return publish_miniverse_control_event(miniverse_id, EventType(method_id), value)

    async def set(self, miniverse_id: str, method_id: str, value: dict | list):
        key = f"{miniverse_id}.{method_id}"
        old_json_value = await self.redis_store.get(key)
        json_value = json.dumps(value)
        if old_json_value != json_value:
            await self.redis_store.set(key, json_value)
            self._publish_event(miniverse_id, method_id, value)

    async def get(self, miniverse_id: str, method_id: str) -> dict | list:
        return json.loads(await self.redis_store.get(f"{miniverse_id}.{method_id}"))


server_status_store = ServerStatusStore(root_store.with_namespace("server-status"))


class WebSocketMiniverseService:
    def __init__(self, miniverse_id: str, url: str, secret: str):
        self.miniverse_id = miniverse_id
        self.rpc: RpcService = RpcService(url, secret)
        self._add_handlers()

        self.task: asyncio.Task = asyncio.create_task(self.rpc.async_connect_loop())

    def _add_handlers(self) -> None:
        coro_list = [
            self.rpc.async_add_handler("minecraft:notification/players/joined",
                                       callback=self._handle_msmp_player_list),
            self.rpc.async_add_handler("minecraft:notification/players/left",
                                       callback=self._handle_msmp_player_list),

            self.rpc.async_add_handler("minecraft:notification/operators/added",
                                       callback=self._handle_msmp_operator_list),
            self.rpc.async_add_handler("minecraft:notification/operators/removed",
                                       callback=self._handle_msmp_operator_list),

            self.rpc.async_add_handler("minecraft:notification/bans/added",
                                       callback=self._handle_msmp_banned_player_list),
            self.rpc.async_add_handler("minecraft:notification/bans/removed",
                                       callback=self._handle_msmp_banned_player_list),

            self.rpc.async_add_handler("minecraft:notification/server/saving",
                                       callback=self._handle_server_saving),

            self.rpc.async_add_handler("minecraft:notification/server/saved",
                                       callback=self._handle_server_saved),

            self.rpc.async_add_handler("minecraft:notification/server/started",
                                       callback=self._handle_server_started),

            self.rpc.async_add_handler("minecraft:notification/server/stopping",
                                       callback=self._handle_server_stopping),
        ]
        for coro in coro_list:
            asyncio.create_task(coro)

    def on_connect(self):
        coro_list = [
            self.get_msmp_player_list(refresh_cache=True),
            self.get_msmp_operator_list(refresh_cache=True),
            self.get_msmp_banned_player_list(refresh_cache=True),
        ]
        for coro in coro_list:
            asyncio.create_task(coro)

    def stop(self):
        self.task.cancel()

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

    async def _get_data_cached(self, method_id: str, refresh_cache: bool):
        if not refresh_cache:
            raw_data = await server_status_store.get(self.miniverse_id, method_id)
        else:
            raw_data = None

        if raw_data is None:
            raw_data = await self.rpc.async_call_rpc(f"minecraft:{method_id}")
            await server_status_store.set(self.miniverse_id, method_id, raw_data)
        return raw_data

    async def get_msmp_player_list(self, refresh_cache=False) -> list[MSMPPlayer]:
        return [MSMPPlayer(**d) for d in await self._get_data_cached("players", refresh_cache)]

    async def get_msmp_operator_list(self, refresh_cache=False) -> list[MSMPOperator]:
        return [MSMPOperator.from_dict(d) for d in await self._get_data_cached("operators", refresh_cache)]

    async def get_msmp_banned_player_list(self, refresh_cache=False) -> list[MSMPPlayerBan]:
        return [MSMPPlayerBan.from_dict(d) for d in await self._get_data_cached("bans", refresh_cache)]

    async def set_player_operator(self, player_id: str, set_operator: bool):
        if set_operator:
            op = MSMPOperator(permissionLevel=4, bypassesPlayerLimit=True, player=MSMPPlayer(id=player_id, name=""))
            await self.rpc.async_call_rpc("minecraft:operators/add", [op.to_dict()])
        else:
            player = MSMPPlayer(id=player_id, name="")
            await self.rpc.async_call_rpc("minecraft:operators/remove", [player.__dict__])

    async def kick_player(self, player_id: str, reason: str):
        data = {
            'player': {'id': player_id},
            'message': {'literal': reason}
        }
        await self.rpc.async_call_rpc("minecraft:players/kick", [data])

    async def ban_player(self, player_id: str, reason: str):
        data = {
            'player': {'id': player_id},
            'reason': reason  #
        }
        await self.rpc.async_call_rpc("minecraft:bans/add", [data])

    async def unban_player(self, player_id: str):
        data = {'id': player_id}
        await self.rpc.async_call_rpc("minecraft:bans/remove", [data])
