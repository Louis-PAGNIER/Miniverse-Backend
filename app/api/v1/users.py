from litestar import get, post, Controller
from litestar.di import Provide
from litestar.params import Dependency
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import User
from app.schemas import UserRegistrationSchema
from app.schemas.user import UserCreateDTO, UserReadDTO
from app.services.user_service import create_user, get_users


class UsersController(Controller):
    path = "/users"
    dependencies = {"db": Provide(get_db_session)}
    return_dto = UserReadDTO

    @get("/")
    async def list_users(self, db: AsyncSession) -> list[User]:
        return await get_users(db)

    @post("/")
    async def create_user(self, data: UserRegistrationSchema, db: AsyncSession) -> User:
        return await create_user(data, db)
