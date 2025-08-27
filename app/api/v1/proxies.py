from litestar import get, post, Controller
from litestar.di import Provide
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Proxy
from app.schemas import ProxyRead, ProxyCreate
from app.services.proxy_service import create_proxy, get_proxies


class ProxiesController(Controller):
    path = "/proxies"
    tags = ["Proxies"]
    dependencies = {"db": Provide(get_db_session)}
    return_dto = ProxyRead

    @get("/")
    async def list_proxies(self, db: AsyncSession) -> list[Proxy]:
        return await get_proxies(db)

    @post("/")
    async def create_proxy(self, data: ProxyCreate, db: AsyncSession) -> Proxy:
        return await create_proxy(data, db)
