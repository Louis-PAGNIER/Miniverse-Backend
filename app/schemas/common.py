from uuid import UUID

from pydantic import BaseModel

from app.enums import Role
from app.schemas import UserReadMinimal


class UserRoleBase(BaseModel):
    role: Role

class UserRoleCreate(UserRoleBase):
    user_id: UUID
    miniverse_id: UUID | None = None
    proxy_id: UUID | None = None

class UserRoleRead(UserRoleBase):
    user: UserReadMinimal

    class Config:
        from_attributes = True