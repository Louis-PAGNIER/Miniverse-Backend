from litestar import get, post, Controller, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException, NotAuthorizedException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.enums import Role
from app.models import Proxy, User
from app.schemas import ProxyCreate
from app.services.auth_service import admin_user_guard, get_current_user
from app.services.proxy_service import create_proxy, get_proxies, get_proxy, delete_proxy


class ProxiesController(Controller):
    path = "/proxies"
    tags = ["Proxies"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }

    @get("/")
    async def list_proxies(self, db: AsyncSession) -> list[Proxy]:
        return await get_proxies(db)

    @post("/", guards=[admin_user_guard])
    async def create_proxy(self, data: ProxyCreate, db: AsyncSession) -> Proxy:
        return await create_proxy(data, db)

    @delete("/{proxy_id:str}")
    async def delete_proxy(self, current_user: User, proxy_id: str, db: AsyncSession) -> None:
        if current_user.get_proxy_role(proxy_id) < Role.ADMIN:
            raise NotAuthorizedException("You are not authorized to delete this proxy")
        proxy = await get_proxy(proxy_id, db)
        await delete_proxy(proxy, db)
        return None