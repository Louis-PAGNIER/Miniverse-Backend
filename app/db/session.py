from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False)

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)

async def get_db_session() -> AsyncGenerator[AsyncSession]:
    async with async_session_factory() as session:
        yield session
