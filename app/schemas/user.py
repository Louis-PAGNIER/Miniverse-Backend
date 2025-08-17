from pydantic import BaseModel
from uuid import UUID

from app.enums import Role


class UserBase(BaseModel):
    username: str
    role: Role = Role.USER

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None

class UserReadMinimal(UserBase):  # utile dans MiniverseRead
    id: UUID

    class Config:
        from_attributes = True

class UserRead(UserReadMinimal):
    pass