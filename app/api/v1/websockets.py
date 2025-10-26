import json
from dataclasses import dataclass

from litestar import websocket, WebSocket
from litestar.channels import ChannelsPlugin
from litestar.di import Provide
from litestar.exceptions import WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from websockets import ConnectionClosedError

from app import get_db_session
from app.enums import Role
from app.models import User
from app.services.docker_service import dockerctl
from app.services.miniverse_service import get_miniverse
from app.services.user_service import get_user

# TODO: move in a more general file
@dataclass
class WebsocketContext:
    user: User


async def handle_miniverse_channel_message(message: bytes, socket: WebSocket, db: AsyncSession, ctx: WebsocketContext) -> None:
    data = json.loads(message)
    miniverse_id = data.get("miniverse-id")
    event_type = data.get("type")

    if event_type == "deleted":
        await socket.send_json(data)
        return

    if event_type in ["created", "updated"]:
        ctx.user = await get_user(socket.user.id, db)

    if miniverse_id is None or ctx.user.get_miniverse_role(miniverse_id) >= Role.USER:
        await socket.send_json(data)


@websocket("/ws/miniverse", dependencies={"db": Provide(get_db_session)})
async def websocket_miniverse_updates_handler(socket: WebSocket, channels: ChannelsPlugin, db: AsyncSession) -> None:
    await socket.accept()
    ctx = WebsocketContext(socket.user)
    try:
        async with channels.start_subscription(["miniverse-updates"]) as subscriber, subscriber.run_in_background(
                lambda msg: handle_miniverse_channel_message(msg, socket, db, ctx)
        ):
            while (response := await socket.receive_text()) is not None:
                print(response)  # TODO: Future usage
    except (WebSocketDisconnect, ConnectionClosedError):
        pass
    except Exception as e:
        print(f"Error in WebSocket: {e}")


@websocket("/ws/miniverse/logs/{miniverse_id:str}", dependencies={"db": Provide(get_db_session)})
async def websocket_miniverse_logs_handler(miniverse_id: str, socket: WebSocket, db: AsyncSession) -> None:
    await socket.accept()
    try:
        miniverse = await get_miniverse(miniverse_id, db)
        user = await get_user(socket.user.id, db)
        #if user.get_miniverse_role(miniverse_id) >= Role.MODERATOR:
        async for chunk in dockerctl.get_container_logs_generator(miniverse.container_id):
            if chunk is not None:
                await socket.send_text(chunk)
    except (WebSocketDisconnect, ConnectionClosedError):
        pass
    except Exception as e:
        print(f"Error in WebSocket: {e}")
