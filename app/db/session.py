from typing import AsyncGenerator

from advanced_alchemy.config import AsyncSessionConfig
from litestar.plugins.sqlalchemy import SQLAlchemyAsyncConfig
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:////app/data/database.db"

session_config = SQLAlchemyAsyncConfig(
    connection_string=SQLALCHEMY_DATABASE_URL,
    create_all=True,
    metadata=Base.metadata,
    session_config=AsyncSessionConfig(expire_on_commit=False)
)

async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with session_config.get_session() as session:
        yield session
