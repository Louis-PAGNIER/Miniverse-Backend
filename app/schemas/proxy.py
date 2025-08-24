from dataclasses import dataclass

from advanced_alchemy.extensions.litestar import SQLAlchemyDTO

from app.enums import ProxyType
from app.models import Proxy


@dataclass
class ProxyCreate:
    name: str
    type: ProxyType
    port: int
    description: str | None = None


class ProxyRead(SQLAlchemyDTO[Proxy]):
    ...

