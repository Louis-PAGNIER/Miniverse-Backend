from app import logger
from app.core import root_store
from app.core.utils import websocket_uri_from_miniverse_id
from app.models import Miniverse
from app.services.websocket_miniverse_service import WebSocketMiniverseService

server_status_store = root_store.with_namespace("server-status")


class MiniversesManager:
    def __init__(self):
        self._miniverse_control_services: dict[str, WebSocketMiniverseService] = dict()

    def add_miniverse(self, miniverse: Miniverse):
        if miniverse.id in self._miniverse_control_services:
            logger.warn("Trying to add a miniverse that already have a control service")
            return

        control = WebSocketMiniverseService(miniverse.id, websocket_uri_from_miniverse_id(miniverse.id),
                                            miniverse.management_server_secret)
        self._miniverse_control_services[miniverse.id] = control

    def remove_miniverse(self, miniverse_id: str):
        control = self._miniverse_control_services.pop(miniverse_id, None)
        if control is not None:
            control.stop()
        logger.info(f"Stopped searching for {miniverse_id} management server")

    def get_miniverse_controler(self, miniverse_id: str):
        return self._miniverse_control_services.get(miniverse_id, None)


miniverses_manager = MiniversesManager()
