from uuid import UUID
from dataclasses import dataclass
from litestar.plugins.sqlalchemy import SQLAlchemyDTO
from litestar.dto import DTOConfig, DataclassDTO

from app.enums import Role
from app.models import User

@dataclass
class UserRegistrationSchema:
    username: str
    password: str
    role: Role = Role.USER

class UserCreateDTO(DataclassDTO[UserRegistrationSchema]):
    ...

class UserReadDTO(SQLAlchemyDTO[User]):
    config = DTOConfig(exclude={"id", "hashed_password"})
