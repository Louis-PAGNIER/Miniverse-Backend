from dataclasses import dataclass
from app.enums import ProxyType


@dataclass
class ProxyCreate:
    name: str
    type: ProxyType
    port: int
    description: str | None = None
