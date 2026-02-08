from litestar import get, Controller, delete, put, post
from litestar.di import Provide
from litestar.exceptions import PermissionDeniedException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.enums import Role
from app.models import User
from app.schemas.user import RoleSchema
from app.services.auth_service import get_current_user, admin_user_guard
from app.services.user_service import get_users, get_user, delete_user, set_user_role, count_admins, get_inactive_users, \
    accept_user_request, reject_user_request


class SelfUserController(Controller):
    path = "/api/users"
    tags = ["Users"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }

    @get("/me")
    async def get_me(self, current_user: User) -> User:
        return current_user

    @delete("/me")
    async def delete_me(self, current_user: User, db: AsyncSession) -> None:
        if current_user.role == Role.ADMIN and await count_admins(db) <= 1:
            raise PermissionDeniedException("You are the only remaining admin")
        await delete_user(current_user.id, db)

class UsersController(Controller):
    path = "/api/users"
    tags = ["Users"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }
    guards = [admin_user_guard]

    @get("/")
    async def list_users(self, db: AsyncSession) -> list[User]:
        return await get_users(db)

    @get("/{user_id:str}")
    async def get_user(self, user_id: str, db: AsyncSession) -> User | None:
        return await get_user(user_id, db)

    @delete("/{user_id:str}")
    async def delete_user(self, user_id: str, current_user: User, db: AsyncSession) -> None:
        if current_user.id == user_id:
            raise PermissionDeniedException("You cannot delete yourself")
        await delete_user(user_id, db)

    @put("/{user_id:str}/role")
    async def set_user_role(self, user_id: str, current_user: User, data: RoleSchema, db: AsyncSession) -> None:
        if current_user.id == user_id and await count_admins(db) <= 1:
            raise PermissionDeniedException("You are the only remaining admin")
        await set_user_role(user_id, data.role, db)

    @get("/inactive")
    async def list_inactive_users(self, db: AsyncSession) -> list[User]:
        return await get_inactive_users(db)

    @post("/inactive/accept/{user_id:str}")
    async def accept_user_request(self, user_id: str, db: AsyncSession) -> None:
        await accept_user_request(user_id, db)

    @post("/inactive/reject/{user_id:str}")
    async def reject_user_request(self, user_id: str, db: AsyncSession) -> None:
        await reject_user_request(user_id, db)