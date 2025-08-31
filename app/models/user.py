from litestar.dto import dto_field
from sqlalchemy import String, Enum
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.db import Base
from uuid import uuid4

from app.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()), info=dto_field("read-only"))
    username: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False, info=dto_field("private"))
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.USER)

    miniverses_roles = relationship("MiniverseUserRole", back_populates="user", cascade="all, delete-orphan", lazy="selectin", info=dto_field("private"))
    proxies_roles = relationship("ProxyUserRole", back_populates="user", cascade="all, delete-orphan", lazy="selectin", info=dto_field("private"))