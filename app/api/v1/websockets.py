import json

from litestar import websocket, WebSocket
from litestar.channels import ChannelsPlugin
from litestar.exceptions import WebSocketDisconnect
from websockets import ConnectionClosedError

from app.enums import Role


async def handle_miniverse_channel_message(socket: WebSocket, message: bytes) -> None:
    data = json.loads(message)
    miniverse_id = data.get("miniverse-id")

    if miniverse_id is None or socket.user.get_miniverse_role(miniverse_id) >= Role.USER:
        await socket.send_json(data)

@websocket("/ws/miniverse")
async def websocket_miniverse_updates_handler(socket: WebSocket, channels: ChannelsPlugin) -> None:
    await socket.accept()
    try:
        async with channels.start_subscription(["miniverse-updates"]) as subscriber, subscriber.run_in_background(
            lambda msg: handle_miniverse_channel_message(socket, msg)
        ):
            while True:
                response = await socket.receive_text()
                print(response)
    except (WebSocketDisconnect, ConnectionClosedError):
        pass
    except Exception as e:
        print(f"Error in WebSocket: {e}")
