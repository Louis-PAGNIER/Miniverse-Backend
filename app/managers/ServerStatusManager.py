import asyncio
import json
from dataclasses import dataclass

import websockets

from app import logger
from app.core import root_store
from app.events.miniverse_events import publish_miniverse_players_event
from app.models import Miniverse
from app.schemas import Player

server_status_store = root_store.with_namespace("server-status")

@dataclass
class ManagementServerEvent:
    method: str

def uri_from_miniverse_id(miniverse_id: str) -> str:
    return f"ws://miniverse-{miniverse_id}:25585"

class ServerStatusManager:
    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}
        self.timeouts: dict[str, float] = {}
        self.tries: dict[str, int] = {}
        self.secrets: dict[str, str] = {}

    def reset_tries(self, miniverse_id: str):
        self.tries[miniverse_id] = 0
        self.timeouts[miniverse_id] = 3.0

    def get_next_timeout_and_increment(self, miniverse_id: str) -> float:
        thresholds = [
            (30, 60.0),
            (20, 30.0),
            (15, 10.0),
            (0, 3.0)
        ]
        if miniverse_id not in self.tries:
            self.reset_tries(miniverse_id)
        self.tries[miniverse_id] += 1
        tries = self.tries[miniverse_id]
        timeout = next((t for (s, t) in thresholds if tries > s))
        self.timeouts[miniverse_id] = timeout
        return timeout

    def get_ws_connection(self, miniverse_id: str):
        headers = {"Authorization": f"Bearer {self.secrets[miniverse_id]}"}
        uri = uri_from_miniverse_id(miniverse_id)
        return websockets.connect(uri, additional_headers=headers)

    def add_miniverse(self, miniverse: Miniverse):
        miniverse_id = miniverse.id
        if miniverse_id not in self.tasks:
            self.secrets[miniverse_id] = miniverse.management_server_secret
            self.tasks[miniverse_id] = asyncio.create_task(self._run_client(miniverse_id))
            self.reset_tries(miniverse_id)
            logger.info(f"Started searching for {miniverse_id} management server")

    def remove_miniverse(self, miniverse_id: str):
        if miniverse_id in self.tasks:
            self.tasks[miniverse_id].cancel()
            del self.tasks[miniverse_id]
            logger.info(f"Stopped searching for {miniverse_id} management server")

    @staticmethod
    async def get_players_list(ws) -> list[Player]:
        await ws.send(json.dumps({"method": "minecraft:players", "id": 1}))
        return json.loads(await ws.recv()).get("result", [])

    async def _run_client(self, miniverse_id: str):
        while True:
            try:
                async with self.get_ws_connection(miniverse_id) as ws:
                    self.reset_tries(miniverse_id)
                    logger.info(f"Successfully connected to management server for miniverse {miniverse_id}")
                    players_list = await self.get_players_list(ws)
                    await server_status_store.set(f"{miniverse_id}.players", json.dumps(players_list))
                    publish_miniverse_players_event(miniverse_id, players_list)

                    async for message in ws:
                        data = json.loads(message)
                        await self.handle_management_server_event(miniverse_id, data)
            except Exception as e:
                timeout = self.get_next_timeout_and_increment(miniverse_id)
                await asyncio.sleep(timeout)


    async def handle_management_server_event(self, miniverse_id: str, data: dict):
        if (method := data.get("method")) is None:
            return

        if method in ["minecraft:notification/players/joined", "minecraft:notification/players/left"]:
            async with self.get_ws_connection(miniverse_id) as ws:
                players_list = await self.get_players_list(ws)
                await server_status_store.set(f"{miniverse_id}.players", json.dumps(players_list))
                publish_miniverse_players_event(miniverse_id, players_list)

        elif method == "minecraft:notification/server/saving":
            logger.info(f"Server save started for miniverse {miniverse_id}")

        elif method == "minecraft:notification/server/saved":
            logger.info(f"Server save completed for miniverse {miniverse_id}")

        elif method == "minecraft:notification/server/started":
            logger.info(f"Miniverse {miniverse_id} started")

        elif method == "minecraft:notification/server/stopping":
            logger.info(f"Miniverse {miniverse_id} is stopping...")

        else:
            # rich.print_json(data=data) # For debugging purposes
            pass


server_status_manager = ServerStatusManager()