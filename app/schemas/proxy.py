from dataclasses import dataclass

from advanced_alchemy.extensions.litestar import SQLAlchemyDTO
from litestar.dto import DTOConfig

from app.enums import ProxyType
from app.models import Proxy


class ProxyRead(SQLAlchemyDTO[Proxy]):
    config = DTOConfig(exclude={"miniverses", "users_roles"})


@dataclass
class ProxyCreate:
    name: str
    type: ProxyType
    port: int
    description: str | None = None
