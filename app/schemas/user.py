from dataclasses import dataclass
from litestar.dto import DataclassDTO
from app.enums import Role


@dataclass
class UserCreate:
    username: str
    password: str
    role: Role = Role.USER
UserCreateDTO = DataclassDTO[UserCreate]
