from litestar import Controller, post

from app.managers import miniverses_manager


class MCRouterController(Controller):
    path = "/api-internal/mc-router"
    tags = ["MCRouter"]

    @post(guards=[])
    async def receive_webhook(self, data: dict) -> None:
        await miniverses_manager.handle_mc_router_webhook(data)