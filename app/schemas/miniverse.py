from pydantic import BaseModel
from uuid import UUID
from app.schemas.common import UserRoleRead


class MiniverseBase(BaseModel):
    name: str
    type: str
    description: str | None = None
    container_id: str | None = None
    mc_version: str
    subdomain: str

class MiniverseCreate(MiniverseBase):
    proxy_id: UUID | None = None

class MiniverseUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    mc_version: str | None = None
    subdomain: str | None = None
    proxy_id: UUID | None = None

class MiniverseRead(MiniverseBase):
    id: UUID
    proxy_id: UUID | None
    user_roles: list["UserRoleRead"] = []

    class Config:
        from_attributes = True