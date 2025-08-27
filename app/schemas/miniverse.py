from dataclasses import dataclass

from advanced_alchemy.extensions.litestar import SQLAlchemyDTO
from litestar.dto import DTOConfig

from app.enums import MiniverseType
from app.models import Miniverse


class MiniverseRead(SQLAlchemyDTO[Miniverse]):
    config = DTOConfig(exclude={"users_roles", "proxy"})


@dataclass
class MiniverseCreate:
    name: str
    type: MiniverseType
    description: str | None
    mc_version: str
    subdomain: str | None
    proxy_id: str | None