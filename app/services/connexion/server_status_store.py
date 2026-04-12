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
