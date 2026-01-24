import json

from litestar import get, post, Controller, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException, NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.enums import Role
from app.managers.ServerStatusManager import server_status_store
from app.models import Miniverse, Mod, User
from app.schemas import MiniverseCreate, ModUpdateInfo, MiniverseUpdateMCVersion, Player, AutomaticInstallMod, \
    MSMPPlayerBan
from app.services.auth_service import get_current_user
from app.services.miniverse_service import create_miniverse, get_miniverses, delete_miniverse, get_miniverse, \
    start_miniverse, stop_miniverse, restart_miniverse, update_miniverse, miniverse_set_player_operator, \
    miniverse_kick_player, miniverse_ban_player, miniverse_unban_player
from app.services.mods_service import get_mod, install_mod, uninstall_mod, update_mod, list_possible_mod_updates, \
    automatic_mod_install


class MiniversesController(Controller):
    path = "/api/miniverses"
    tags = ["Miniverses"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }

    @get("/")
    async def list_miniverses(self, current_user: User, db: AsyncSession) -> list[Miniverse]:
        miniverses = await get_miniverses(db)
        return [m for m in miniverses if current_user.get_miniverse_role(m.id) >= Role.USER]

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

    @post("/{miniverse_id:str}/start")
    async def start_miniverse(self, current_user: User, miniverse_id: str, db: AsyncSession) -> Miniverse:
        if current_user.get_miniverse_role(miniverse_id) < Role.USER:
            raise NotAuthorizedException("You are not authorized to start this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        if miniverse is None:
            raise NotFoundException("Miniverse not found")

        await start_miniverse(miniverse, db)

        return miniverse

    @post("/{miniverse_id:str}/stop")
    async def stop_miniverse(self, current_user: User, miniverse_id: str, db: AsyncSession) -> Miniverse:
        if current_user.get_miniverse_role(miniverse_id) < Role.USER:
            raise NotAuthorizedException("You are not authorized to stop this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        if miniverse is None:
            raise NotFoundException("Miniverse not found")

        await stop_miniverse(miniverse, db)

        return miniverse

    @post("/{miniverse_id:str}/restart")
    async def restart_miniverse(self, current_user: User, miniverse_id: str, db: AsyncSession) -> Miniverse:
        if current_user.get_miniverse_role(miniverse_id) < Role.USER:
            raise NotAuthorizedException("You are not authorized to restart this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        if miniverse is None:
            raise NotFoundException("Miniverse not found")

        await restart_miniverse(miniverse, db)

        return miniverse

    @post("/{miniverse_id:str}/update_mc_version")
    async def update_miniverse(self, current_user: User, miniverse_id: str, data: MiniverseUpdateMCVersion,
                               db: AsyncSession) -> Miniverse:
        if current_user.get_miniverse_role(miniverse_id) < Role.ADMIN:
            raise NotAuthorizedException("You are not authorized to update this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        if miniverse is None:
            raise NotFoundException("Miniverse not found")

        return await update_miniverse(miniverse, data.mc_version, db)

    @post("/{miniverse_id:str}/install/mod")
    async def automatic_install_mod(self, current_user: User, miniverse_id: str, data: AutomaticInstallMod,
                                    db: AsyncSession) -> Mod:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to install mods in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        return await automatic_mod_install(data.mod_id, miniverse, db, retry_with_latest=True)

    @post("/{miniverse_id:str}/install/mod/{mod_version_id:str}")
    async def install_mod(self, current_user: User, miniverse_id: str, mod_version_id: str, db: AsyncSession) -> Mod:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to install mods in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        return await install_mod(mod_version_id, miniverse, db)

    @delete("/mods/{mod_id:str}")
    async def uninstall_mod(self, current_user: User, mod_id: str, db: AsyncSession) -> None:
        if (mod := await get_mod(mod_id, db)) is None:
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
    async def list_mod_updates(self, current_user: User, miniverse_id: str, db: AsyncSession) -> dict[
        str, ModUpdateInfo]:
        if current_user.get_miniverse_role(miniverse_id) < Role.USER:
            raise NotAuthorizedException("You are not authorized to view mod updates in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return await list_possible_mod_updates(miniverse)

    @get("/players")
    async def list_all_players(self, current_user: User, db: AsyncSession) -> dict[str, list[Player]]:
        miniverses = await get_miniverses(db)
        miniverses = [m for m in miniverses if current_user.get_miniverse_role(m.id) >= Role.USER]

        result: dict[str, list[Player]] = {}
        for miniverse in miniverses:
            if not miniverse.started:
                result[miniverse.id] = []
                continue

            json_raw = await server_status_store.get(f"{miniverse.id}.players")
            if json_raw is None:
                result[miniverse.id] = []
            else:
                result[miniverse.id] = json.loads(json_raw)

        return result

    @get("/players/banned")
    async def list_all_banned_players(self, current_user: User, db: AsyncSession) -> dict[str, list[MSMPPlayerBan]]:
        miniverses = await get_miniverses(db)
        miniverses = [m for m in miniverses if current_user.get_miniverse_role(m.id) >= Role.USER]

        result: dict[str, list[MSMPPlayerBan]] = {}
        for miniverse in miniverses:
            if not miniverse.started:
                result[miniverse.id] = []
                continue

            json_raw = await server_status_store.get(f"{miniverse.id}.bans")
            if json_raw is None:
                result[miniverse.id] = []
            else:
                result[miniverse.id] = json.loads(json_raw)

        return result

    @post("/{miniverse_id:str}/operator")
    async def set_operator(self, current_user: User, miniverse_id: str, player_id: str, db: AsyncSession,
                           value: bool = True) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to set operators in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        await miniverse_set_player_operator(miniverse, player_id, value)

    @post("/{miniverse_id:str}/kick")
    async def kick_player(self, current_user: User, miniverse_id: str, player_id: str, db: AsyncSession,
                          reason: str = 'You have been kicked by an administrator') -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to kick players in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        await miniverse_kick_player(miniverse, player_id, reason)

    @post("/{miniverse_id:str}/ban")
    async def ban_player(self, current_user: User, miniverse_id: str, player_id: str, db: AsyncSession,
                         reason: str = 'You have been banned by an administrator') -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to ban players in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        await miniverse_ban_player(miniverse, player_id, reason)

    @post("/{miniverse_id:str}/unban")
    async def unban_player(self, current_user: User, miniverse_id: str, player_id: str, db: AsyncSession) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to unban players in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        await miniverse_unban_player(miniverse, player_id)
