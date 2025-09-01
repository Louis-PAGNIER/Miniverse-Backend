from litestar import get, post, Controller, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Proxy
from app.schemas import ProxyCreate
from app.services.proxy_service import create_proxy, get_proxies, get_proxy, delete_proxy


class ProxiesController(Controller):
    path = "/proxies"
    tags = ["Proxies"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/")
    async def list_proxies(self, db: AsyncSession) -> list[Proxy]:
        return await get_proxies(db)

    @post("/")
    async def create_proxy(self, data: ProxyCreate, db: AsyncSession) -> Proxy:
        return await create_proxy(data, db)

    @delete("/{proxy_id:str}")
    async def delete_proxy(self, proxy_id: str, db: AsyncSession) -> None:
        proxy = await get_proxy(proxy_id, db)
        if not proxy:
            raise NotFoundException("Proxy not found")
        await delete_proxy(proxy, db)
        return None