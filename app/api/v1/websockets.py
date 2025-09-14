import base64
import json

from litestar import websocket, WebSocket
from litestar.channels import ChannelsPlugin

from app.enums import Role
from app.models import MiniverseUserRole, User


@websocket("/ws/miniverse-updates")
async def websocket_miniverse_updates_handler(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()

    current_user: User = socket.user

    async with channels.start_subscription(["miniverse-updates"]) as subscriber:
        async for message in subscriber.iter_events():
            data = json.loads(message)
            miniverse_id = data.get("miniverse_id")

            if miniverse_id is None or current_user.get_miniverse_role(miniverse_id) >= Role.USER:
                await socket.send_json(data)