import asyncio

from docker.errors import NotFound
from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.config.response_cache import ResponseCacheConfig
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.types import HTTPScope

from app import logger
from app.api.v1 import UsersController, MiniversesController, ModsController
from app.api.v1.files import FilesController
from app.api.v1.minecraft import MinecraftController
from app.api.v1.users import SelfUserController
from app.api.v1.websockets import websocket_miniverse_updates_handler, websocket_miniverse_logs_handler
from app.core.channels import channels_plugin
from app.db import Base
from app.db.session import session_config
from app.managers.ServerStatusManager import server_status_manager
from app.services.auth_service import jwtAuth
from app.services.docker_service import dockerctl
from app.services.miniverse_service import get_miniverses, start_miniverse, stop_miniverse_container
from app.services.proxy_service import start_proxy_containers, update_proxy_config, stop_proxy_containers


async def proxy_startup():
    async with session_config.get_session() as session:
        await update_proxy_config(session)


async def db_startup():
    async with session_config.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def server_status_manager_startup():
    async with session_config.get_session() as session:
        miniverses = await get_miniverses(session)
        for miniverse in miniverses:
            if miniverse.started:
                server_status_manager.add_miniverse(miniverse)


async def docker_startup():
    await start_proxy_containers()
    async with session_config.get_session() as session:
        miniverses = await get_miniverses(session)
        for miniverse in miniverses:
            if miniverse.started:
                await start_miniverse(miniverse, session)


async def docker_shutdown():
    async with session_config.get_session() as session:
        miniverses = await get_miniverses(session)

        tasks = [
            stop_miniverse_container(miniverse)
            for miniverse in miniverses
        ]
        tasks.append(stop_proxy_containers())
        try:
            await asyncio.gather(*tasks)
        except NotFound as e:
            logger.error(e)
    await dockerctl.close()


def custom_cache_response_filter(_: HTTPScope, status_code: int) -> bool:
    # Cache only 2xx responses
    return 200 <= status_code < 300


response_cache_config = ResponseCacheConfig(cache_response_filter=custom_cache_response_filter)

cors_config = CORSConfig(allow_origins=["*"], allow_credentials=True)  # TODO: do cleaner CORS config

app = Litestar(
    cors_config=cors_config,
    response_cache_config=response_cache_config,
    route_handlers=[UsersController, SelfUserController, MiniversesController, FilesController, ModsController, MinecraftController,
                    websocket_miniverse_updates_handler, websocket_miniverse_logs_handler],
    on_startup=[db_startup, proxy_startup, docker_startup, server_status_manager_startup],
    on_shutdown=[docker_shutdown],  # TODO: Do we really need to shutdown all containers ?
    on_app_init=[jwtAuth.on_app_init],
    openapi_config=OpenAPIConfig(
        title="Miniverse API",
        version="0.0.1",
        description="API for Miniverse, an open source self-hosted server manager.",
        render_plugins=[
            SwaggerRenderPlugin(
                init_oauth={
                    "clientId": "miniverse-client",
                    "appName": "Miniverse",
                    "scopeSeparator": " ",
                    "scopes": "openid profile",
                    "useBasicAuthenticationWithAccessCodeGrant": True,
                    "usePkceWithAuthorizationCodeGrant": True,
                }
            )
        ],
        path="/docs"
    ),
    plugins=[SQLAlchemyPlugin(config=session_config), channels_plugin],
)
