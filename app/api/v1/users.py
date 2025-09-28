from litestar import get, post, Controller
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import User
from app.schemas import UserCreate
from app.services.auth_service import get_current_user, admin_user_guard
from app.services.user_service import create_user, get_users, get_user


class UsersController(Controller):
    path = "/api/users"
    tags = ["Users"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }

    @get("/")
    async def list_users(self, db: AsyncSession) -> list[User]:
        return await get_users(db)

    @get("/{user_id:str}")
    async def get_user(self, user_id: str, db: AsyncSession) -> User | None:
        return await get_user(user_id, db)

    @get("/me")
    async def get_me(self, current_user: User) -> User:
        return current_user

    @post("/", guards=[admin_user_guard])
    async def create_user(self, data: UserCreate, db: AsyncSession) -> User:
        return await create_user(data, db)
