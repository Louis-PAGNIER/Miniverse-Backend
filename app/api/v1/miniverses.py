from litestar import get, post, Controller, delete
from litestar.di import Provide
from litestar.exceptions import NotFoundException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.models import Miniverse
from app.schemas import MiniverseRead, MiniverseCreate
from app.services.miniverse_service import create_miniverse, get_miniverses, delete_miniverse, get_miniverse


class MiniversesController(Controller):
    path = "/miniverses"
    tags = ["Miniverses"]
    dependencies = {"db": Provide(get_db_session)}
    return_dto = MiniverseRead

    @get("/")
    async def list_miniverses(self, db: AsyncSession) -> list[Miniverse]:
        return await get_miniverses(db)

    @post("/")
    async def create_miniverse(self, data: MiniverseCreate, db: AsyncSession) -> Miniverse:
        return await create_miniverse(data, db)

    @delete('/{miniverse_id:str}')
    async def delete_miniverse(self, miniverse_id: str, db: AsyncSession) -> None:
        miniverse = await get_miniverse(miniverse_id, db)
        if not miniverse:
            raise NotFoundException("Miniverse not found")
        await delete_miniverse(miniverse, db)
        return None