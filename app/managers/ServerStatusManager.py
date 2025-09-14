import asyncio
import json
from collections.abc import Callable

import rich
import websockets

from app import logger
from app.core import root_store
from app.models import Miniverse

server_status_store = root_store.with_namespace("server-status")


def uri_from_miniverse_id(miniverse_id: str) -> str:
    return f"ws://miniverse-{miniverse_id}:25585"


class ServerStatusManager:
    def __init__(self):
        self.tasks: dict[str, asyncio.Task] = {}
        self.timeouts: dict[str, float] = {}
        self.tries: dict[str, int] = {}

    def add_miniverse(self, miniverse: Miniverse):
        miniverse_id = miniverse.id
        if miniverse_id not in self.tasks:
            self.tasks[miniverse_id] = asyncio.create_task(self._run_client(miniverse_id, miniverse.management_server_secret))
            self.tries[miniverse_id] = 0
            self.timeouts[miniverse_id] = 3.0

    def remove_miniverse(self, miniverse_id: str):
        if miniverse_id in self.tasks:
            self.tasks[miniverse_id].cancel()
            del self.tasks[miniverse_id]

    async def _run_client(self, miniverse_id: str, secret: str):
        headers = {"Authorization": f"Bearer {secret}"}
        uri = uri_from_miniverse_id(miniverse_id)

        def get_ws_connection():
            return websockets.connect(uri, additional_headers=headers)

        while True:
            try:
                async with websockets.connect(uri, additional_headers=headers) as ws:
                    self.tries[miniverse_id] = 0
                    self.timeouts[miniverse_id] = 3.0
                    logger.info(f"Successfully connected to management server for miniverse {miniverse_id}")
                    await send_players_list_request(ws)
                    async for message in ws:
                        data = json.loads(message)
                        await handle_management_server_event(miniverse_id, data, get_ws_connection)
            except Exception as e:
                # Connection tries: timeout
                thresholds = [
                    (30, 60.0),
                    (20, 30.0),
                    (15, 10.0),
                    (0, 3.0)
                ]
                print(e)
                self.tries[miniverse_id] += 1
                tries = self.tries[miniverse_id]
                timeout = next((t for (s, t) in thresholds if tries > s))
                self.timeouts[miniverse_id] = timeout
                await asyncio.sleep(timeout)


async def send_players_list_request(ws):
    await ws.send(json.dumps({"id": 1, "method": "minecraft:players"}))

async def handle_management_server_event(miniverse_id: str, data: dict, get_ws_connection: Callable):
    if data.get("method") in ["notification:players/joined", "notification:players/left"]:
        async with get_ws_connection() as ws:
            await send_players_list_request(ws)
            players = json.loads(await ws.recv()).get("result")
            if players is not None:
                logger.info(f"Players list updated for miniverse {miniverse_id}: {[p['name'] for p in players]}")
                await server_status_store.set(f"{miniverse_id}.players", json.dumps(players))
    elif data.get("method") == "notification:server/saving":
        logger.info(f"Server save started for miniverse {miniverse_id}")
    elif data.get("method") == "notification:server/saved":
        logger.info(f"Server save completed for miniverse {miniverse_id}")
    else:
        #rich.print_json(data=data) # For debugging purposes
        pass

server_status_manager = ServerStatusManager()