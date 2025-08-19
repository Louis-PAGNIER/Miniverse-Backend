from dataclasses import dataclass
from litestar.plugins.sqlalchemy import SQLAlchemyDTO
from litestar.dto import DTOConfig

from app.enums import Role
from app.models import User


@dataclass
class UserCreate:
    username: str
    password: str
    role: Role = Role.USER


class UserRead(SQLAlchemyDTO[User]):
    config = DTOConfig(exclude={"hashed_password"})
