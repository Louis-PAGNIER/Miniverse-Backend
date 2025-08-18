from contextlib import asynccontextmanager
from typing import AsyncGenerator

from litestar import Litestar
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin

from app.db import Base, engine
from app.api.v1 import UsersController


@asynccontextmanager
async def db_lifespan(app: Litestar) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = Litestar(
    route_handlers=[UsersController],
    lifespan=[db_lifespan],
    openapi_config=OpenAPIConfig(
        title="Miniverse API",
        version="0.0.1",
        description="API for Miniverse, a decentralized social network.",
        render_plugins=[SwaggerRenderPlugin()],
        path="/docs"
    )
)

