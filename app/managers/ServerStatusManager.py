import asyncio
import json
from collections.abc import Callable

import rich
import websockets

from app.models import Miniverse

def uri_from_miniverse_id(miniverse_id: str) -> str:
    return f"ws://miniverse-{miniverse_id}:25585"


class ServerStatusManager:
    def __init__(self):
        self.tasks = {}

    def add_miniverse(self, miniverse: Miniverse):
        miniverse_id = miniverse.id
        if miniverse_id not in self.tasks:
            self.tasks[miniverse_id] = asyncio.create_task(self._run_client(miniverse_id, miniverse.management_server_secret))

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
                    async for message in ws:
                        data = json.loads(message)
                        await handle_management_server_event(miniverse_id, data, get_ws_connection)
                        print(data)
            except Exception as e:
                print("Connection failed, retrying in 60s...")
                print(e)
                print(uri, secret)
                await asyncio.sleep(60)

async def handle_management_server_event(miniverse_id: str, data: dict, get_ws_connection: Callable):
    uri = uri_from_miniverse_id(miniverse_id)
    if data.get("method") in ["notification:players/joined", "notification:players/left"]:
        # send a request to get current players
        async with get_ws_connection() as ws:
            await ws.send(json.dumps({"id": 1, "method": "minecraft:players"}))
            players_response_data = json.loads(await ws.recv())
            if "result" in players_response_data:
                players = players_response_data["result"]
                print(f"[i] Current players on {uri}: {[p['name'] for p in players]}[/]")
    else:
        rich.print_json(data=data)

server_status_manager = ServerStatusManager()