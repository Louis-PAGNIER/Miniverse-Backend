from dotenv import load_dotenv

load_dotenv()

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin

from app.db import Base, engine
from app.api.v1 import UsersController
from app.api.v1 import oauth2_auth, login

from app.services.docker_service import dockerctl


@asynccontextmanager
async def db_lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@asynccontextmanager
async def docker_lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    await dockerctl.initialize()
    yield



app = Litestar(
    route_handlers=[login, UsersController],
    lifespan=[db_lifespan, docker_lifespan],
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
    )
)

