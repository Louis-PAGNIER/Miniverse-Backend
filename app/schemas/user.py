from pydantic import BaseModel
from uuid import UUID

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: UUID
    class Config:
        from_attributes = True