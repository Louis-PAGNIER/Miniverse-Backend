from litestar import get, post, Controller, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException, NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.enums import Role
from app.models import Miniverse, Mod, User
from app.schemas import MiniverseCreate, ModUpdateInfo
from app.services.auth_service import get_current_user
from app.services.miniverse_service import create_miniverse, get_miniverses, delete_miniverse, get_miniverse
from app.services.mods_service import get_mod, install_mod, uninstall_mod, update_mod, list_possible_mod_updates


class MiniversesController(Controller):
    path = "/miniverses"
    tags = ["Miniverses"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }

    @get("/")
    async def list_miniverses(self, db: AsyncSession) -> list[Miniverse]:
        return await get_miniverses(db)

    @post("/")
    async def create_miniverse(self, current_user: User, data: MiniverseCreate, db: AsyncSession) -> Miniverse:
        if current_user.role < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to create miniverses")

        return await create_miniverse(data, current_user, db)

    @delete("/{miniverse_id:str}")
    async def delete_miniverse(self, current_user: User, miniverse_id: str, db: AsyncSession) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.ADMIN:
            raise NotAuthorizedException("You are not authorized to delete this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        await delete_miniverse(miniverse, db)
        return None

    @post("/{miniverse_id:str}/install/mod/{mod_version_id:str}")
    async def install_mod(self, current_user: User, miniverse_id: str, mod_version_id: str, db: AsyncSession) -> Mod:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to install mods in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        return await install_mod(mod_version_id, miniverse, db)

    @delete("/mods/{mod_id:str}")
    async def uninstall_mod(self, current_user: User, mod_id: str, db: AsyncSession) -> None:
        if mod := get_mod(mod_id, db) is None:
            raise NotFoundException("Mod not found in this miniverse")

        if current_user.get_miniverse_role(mod.miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to uninstall mods in this miniverse")

        await uninstall_mod(mod, db)
        return None

    @post("/mods/{mod_id:str}/update/{new_version_id:str}")
    async def update_mod(self, current_user: User, mod_id: str, new_version_id: str, db: AsyncSession) -> Mod:
        if mod := get_mod(mod_id, db) is None:
            raise NotFoundException("Mod not found in this miniverse")

        if current_user.get_miniverse_role(mod.miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to update mods in this miniverse")

        return await update_mod(mod, new_version_id, db)

    @get("/{miniverse_id:str}/mods/updates")
    async def list_mod_updates(self, current_user: User, miniverse_id: str, db: AsyncSession) -> dict[str, ModUpdateInfo]:
        if current_user.get_miniverse_role(miniverse_id) < Role.USER:
            raise NotAuthorizedException("You are not authorized to view mod updates in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return await list_possible_mod_updates(miniverse)