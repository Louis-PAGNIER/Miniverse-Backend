from typing import Any

from litestar import get, post, Controller, Request
from litestar.di import Provide
from litestar.security.jwt import Token
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import User
from app.schemas import UserCreate
from app.services.user_service import create_user, get_users


class UsersController(Controller):
    path = "/users"
    tags = ["Users"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/")
    async def list_users(self, request: Request[User, Token, Any], db: AsyncSession) -> list[User]:
        return await get_users(db)

    @post("/")
    async def create_user(self, data: UserCreate, db: AsyncSession) -> User:
        return await create_user(data, db)
