from pydantic import BaseModel
from uuid import UUID

from app.enums import ProxyType
from app.schemas.common import UserRoleRead
from app.schemas.miniverse import MiniverseRead


class ProxyBase(BaseModel):
    name: str
    type: ProxyType
    description: str | None = None
    port: int

class ProxyCreate(ProxyBase):
    pass

class ProxyUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    port: int | None = None

class ProxyRead(ProxyBase):
    id: UUID
    miniverses: list["MiniverseRead"] = []
    users: list["UserRoleRead"] = []

    class Config:
        from_attributes = True