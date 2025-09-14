from dotenv import load_dotenv

from app.db.session import session_config
from app.services.miniverse_service import get_miniverses
from app.services.proxy_service import start_proxy_containers, update_proxy_config

load_dotenv()

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar, Request
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin
from litestar.contrib.sqlalchemy.plugins import SQLAlchemyPlugin

from app.db import Base
from app.api.v1 import oauth2_auth, login
from app.api.v1 import UsersController, MiniversesController, ModsController

from app.services.docker_service import dockerctl
from app.managers.ServerStatusManager import server_status_manager

import httpx

async def proxy_startup():
    async with session_config.get_session() as session:
        await update_proxy_config(session)


async def db_startup():
    async with session_config.get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_config.get_session() as session:
        # Create initial admin user if not exists
        ...

async def docker_startup():
    await dockerctl.initialize()
    await start_proxy_containers()


async def server_status_manager_startup():
    async with session_config.get_session() as session:
        miniverses = await get_miniverses(session)
        for miniverse in miniverses:
            server_status_manager.add_miniverse(miniverse)


@asynccontextmanager
async def httpx_client_lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    app.state.httpx_client = httpx.AsyncClient(timeout=10.0)
    yield
    await app.state.httpx_client.aclose()


def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.httpx_client


app = Litestar(
    route_handlers=[login, UsersController, MiniversesController, ModsController],
    lifespan=[httpx_client_lifespan],
    on_startup=[docker_startup, db_startup, proxy_startup, server_status_manager_startup],
    on_app_init=[oauth2_auth.on_app_init],
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
    plugins=[SQLAlchemyPlugin(config=session_config)],
)

