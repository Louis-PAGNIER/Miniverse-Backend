import asyncio
import json

import rich
import websockets
from websockets import ClientConnection

from app import logger
from app.core import root_store
from app.events.miniverse_event import publish_miniverse_players_event, publish_miniverse_ban_player_event
from app.schemas import MSMPOperator, MSMPPlayerBan, Player, MSMPPlayer
from app.services.rpc_service import RpcService

server_status_store = root_store.with_namespace("server-status")


class WebSocketMiniverseService:
    def __init__(self, miniverse_id: str, url: str, secret: str):
        self.miniverse_id = miniverse_id
        self.rpc: RpcService = RpcService(url, secret)
        self._add_handlers()

        self.task: asyncio.Task = asyncio.create_task(self.rpc.connect_loop())

    def stop(self):
        self.task.cancel()

    def _add_handlers(self) -> None:
        coro_list = [
            self.rpc.add_handler("minecraft:notification/players/joined",
                                 callback=self._handle_msmp_player_list),
            self.rpc.add_handler("minecraft:notification/players/left",
                                 callback=self._handle_msmp_player_list),

            self.rpc.add_handler("minecraft:notification/operators/added",
                                 callback=self._handle_msmp_operators_list),
            self.rpc.add_handler("minecraft:notification/operators/removed",
                                 callback=self._handle_msmp_operators_list),
        ]
        for coro in coro_list:
            asyncio.create_task(coro)

    async def handle_management_server_event(self, miniverse_id: str, data: dict):
        if (method := data.get("method")) is None:
            return

        elif method in ["minecraft:notification/bans/added", "minecraft:notification/bans/removed"]:
            async with self.get_ws_connection(miniverse_id) as ws:
                banned_players = await self.refresh_msmp_banned_players_list(miniverse_id, ws)
                publish_miniverse_ban_player_event(miniverse_id, banned_players)

        elif method == "minecraft:notification/server/saving":
            logger.info(f"Server save started for miniverse {miniverse_id}")

        elif method == "minecraft:notification/server/saved":
            logger.info(f"Server save completed for miniverse {miniverse_id}")

        elif method == "minecraft:notification/server/started":
            logger.info(f"Miniverse {miniverse_id} started")

        elif method == "minecraft:notification/server/stopping":
            logger.info(f"Miniverse {miniverse_id} is stopping...")

        else:
            logger.info(f"Miniverse {miniverse_id} said :")
            rich.print_json(data=data)  # For debugging purposes
            pass

    async def _handle_msmp_player_list(self, data):
        players_list = await self.ask_players_list()
        publish_miniverse_players_event(self.miniverse_id, players_list)

    async def _handle_msmp_operators_list(self, data):
        operators_list = self.ask_msmp_operators_list()
        # players_list = await self.get_players_list(miniverse_id, ws)
        # publish_miniverse_players_event(miniverse_id, players_list)

    async def ask_msmp_operators_list(self) -> list[MSMPOperator]:
        operators_list = await self.rpc.call_rpc("minecraft:operators")
        await server_status_store.set(f"{self.miniverse_id}.operators", json.dumps(operators_list))
        return [MSMPOperator.from_dict(o) for o in operators_list]

    async def ask_msmp_banned_players_list(self, miniverse_id: str, ws: ClientConnection) -> list[MSMPPlayerBan]:
        await ws.send(json.dumps({"method": "minecraft:bans", "id": 1}))
        bans = [MSMPPlayerBan.from_dict(p) for p in json.loads(await ws.recv()).get("result", [])]
        await server_status_store.set(f"{miniverse_id}.bans", json.dumps([p.to_dict() for p in bans]))
        return bans

    async def ask_players_list(self) -> list[Player]:
        raw_msmp_players_list = await self.rpc.call_rpc("minecraft:players")
        msmp_players_list = [MSMPPlayer(**p) for p in raw_msmp_players_list]

        operators_list = await server_status_store.get(f"{self.miniverse_id}.operators")
        if operators_list is None:
            operators_list = await self.ask_msmp_operators_list()
        else:
            operators_list = [MSMPOperator.from_dict(o) for o in json.loads(operators_list)]
        operator_ids = set(o.player.id for o in operators_list)

        players_list = [Player(
            id=p.id,
            name=p.name,
            is_operator=p.id in operator_ids
        ) for p in msmp_players_list]

        await server_status_store.set(f"{self.miniverse_id}.players", json.dumps([p.__dict__ for p in players_list]))
        return players_list

    #
    # @staticmethod
    # async def set_player_operator(miniverse_id: str, player_id: str, is_operator: bool):
    #     if is_operator:
    #         op = MSMPOperator(permissionLevel=4, bypassesPlayerLimit=True, player=MSMPPlayer(id=player_id, name=""))
    #         await ws.send(json.dumps({"method": "minecraft:operators/add", "id": 1, "params": [[op.to_dict()]]}))
    #     else:
    #         player = MSMPPlayer(id=player_id, name="")
    #         await ws.send(json.dumps({"method": "minecraft:operators/remove", "id": 1, "params": [[player.__dict__]]}))
    #     await ws.recv()
    #     await ServerStatusManager.refresh_msmp_operators_list(miniverse_id, ws)

    @staticmethod
    async def kick_player(ws: ClientConnection, player_id: str, reason: str):
        data = {
            'player': {'id': player_id},
            'message': {'literal': reason}
        }
        await ws.send(json.dumps({"method": "minecraft:players/kick", "id": 1, "params": [[data]]}))
        await ws.recv()

    @staticmethod
    async def ban_player(ws: ClientConnection, player_id: str, reason: str):
        data = {
            'player': {'id': player_id},
            'reason': reason
        }
        await ws.send(json.dumps({"method": "minecraft:bans/add", "id": 1, "params": [[data]]}))
        await ws.recv()

    @staticmethod
    async def unban_player(ws: ClientConnection, player_id: str):
        data = {'id': player_id}
        await ws.send(json.dumps({"method": "minecraft:bans/remove", "id": 1, "params": [[data]]}))
        await ws.recv()

    async def _run_client(self, miniverse_id: str):
        while True:  # TODO: Never use while True, this code must timeout after 10min and check each loop if the container we want to connect still exist
            try:
                async with self.get_ws_connection(miniverse_id) as ws:
                    self.reset_tries(miniverse_id)
                    logger.info(f"Successfully connected to management server for miniverse {miniverse_id}")

                    await self.refresh_msmp_operators_list(miniverse_id, ws)
                    await self.refresh_msmp_banned_players_list(miniverse_id, ws)

                    players_list = await self.get_players_list(miniverse_id, ws)
                    publish_miniverse_players_event(miniverse_id, players_list)

                    # TODO refractor the code below in a separate method
                    try:
                        async for message in ws:
                            data = json.loads(message)
                            await self.handle_management_server_event(miniverse_id, data)
                    except websockets.exceptions.ConnectionClosed:
                        return
                    except Exception as e:
                        print(e)  # This should never happen, this is to display strange behaviors
                        exit(1)
            except Exception as e:
                print(e)
                timeout = self.get_next_timeout_and_increment(miniverse_id)
                await asyncio.sleep(timeout)
