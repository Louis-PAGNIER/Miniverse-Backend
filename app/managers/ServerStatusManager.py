from app import logger
from app.core import root_store
from app.core.utils import websocket_uri_from_miniverse_id
from app.models import Miniverse
from app.services.connexion.BaseMiniverseService import BaseMiniverseService
from app.services.connexion.MCRouterMiniverseService import MCRouterMiniverseService
from app.services.connexion.WebSocketMiniverseService import WebSocketMiniverseService
from app.services.minecraft_service import compare_versions

server_status_store = root_store.with_namespace("server-status")


class MiniversesManager:
    def __init__(self):
        self._miniverse_control_services: dict[str, BaseMiniverseService] = dict()

    async def add_miniverse(self, miniverse: Miniverse) -> BaseMiniverseService:
        existing_control = self._miniverse_control_services.get(miniverse.id, None)
        if existing_control is not None:
            existing_control.start()
            return existing_control

        support_websockets = (await compare_versions(miniverse.mc_version, "1.21.9")) == 1
        if support_websockets:
            control = WebSocketMiniverseService(miniverse.id, websocket_uri_from_miniverse_id(miniverse.id),
                                                miniverse.management_server_secret)
        else:
            control = MCRouterMiniverseService(miniverse.id)

        self._miniverse_control_services[miniverse.id] = control
        return control

    async def remove_miniverse(self, miniverse_id: str):
        control = self._miniverse_control_services.pop(miniverse_id, None)
        if control is not None:
            await control.stop()
        logger.info(f"Stopped searching for {miniverse_id} management server")

    def get_miniverse_controller(self, miniverse_id: str) -> BaseMiniverseService | None:
        return self._miniverse_control_services.get(miniverse_id, None)

    async def handle_mc_router_webhook(self, payload: dict):
        target_id = str(payload.get("backend")).lstrip('miniverse-').split(':')[0]
        service = self._miniverse_control_services.get(target_id)
        if service and isinstance(service, MCRouterMiniverseService):
            await service.process_webhook(payload)


miniverses_manager = MiniversesManager()
