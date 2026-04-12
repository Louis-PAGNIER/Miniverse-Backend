from app import logger
from app.schemas import MSMPPlayer
from app.services.connexion.BaseMiniverseService import BaseMiniverseService


class MCRouterMiniverseService(BaseMiniverseService):
    def __init__(self, miniverse_id: str):
        super().__init__(miniverse_id)
        self._online_players: dict[str, MSMPPlayer] = {}

    async def _get_data_from_source(self, method_name: str):
        if method_name == "minecraft:players":
            return [p.model_dump() for p in self._online_players.values()]
        return None

    def start(self):
        logger.info(f"Router service {self.miniverse_id} listening for webhooks")

    async def stop(self):
        self._online_players.clear()

    async def process_webhook(self, payload: dict):
        event_type = payload.get("event")
        player_data = payload.get("player")

        if not player_data:
            return

        p_id = player_data["uuid"]
        p_name = player_data["name"]

        if event_type == "connect" and payload.get("status") == "success":
            self._online_players[p_id] = MSMPPlayer(id=p_id, name=p_name)
            logger.info(f"Player {p_name} joined {self.miniverse_id} via MC-Router")
        elif event_type == "disconnect":
            self._online_players.pop(p_id, None)
            logger.info(f"Player {p_name} disconnected {self.miniverse_id} via MC-Router")
        else:
            logger.info(f"Unknown event {event_type}")

        await self.get_msmp_player_list(refresh_cache=True)