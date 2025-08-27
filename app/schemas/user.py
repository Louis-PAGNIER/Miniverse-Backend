from dataclasses import dataclass

from advanced_alchemy.extensions.litestar import SQLAlchemyDTO
from litestar.dto import DataclassDTO, DTOConfig

from app.enums import Role
from app.models import User


class UserRead(SQLAlchemyDTO[User]):
    config = DTOConfig(exclude={"hashed_password", "miniverses_roles", "proxies_roles"})


@dataclass
class UserCreate:
    username: str
    password: str
    role: Role = Role.USER
UserCreateDTO = DataclassDTO[UserCreate]
