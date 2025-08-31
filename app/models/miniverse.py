from litestar.dto import dto_field
from sqlalchemy import String, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from uuid import uuid4

from app.enums import MiniverseType, Role
from app.models.mod import Mod


class Miniverse(Base):
    __tablename__ = "miniverses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()), info=dto_field("read-only"))
    name: Mapped[str] = mapped_column(String)
    type: Mapped[MiniverseType] = mapped_column(Enum(MiniverseType))
    description: Mapped[str | None] = mapped_column(Text)
    container_id: Mapped[str | None] = mapped_column(String)
    mc_version: Mapped[str] = mapped_column(String)
    subdomain: Mapped[str] = mapped_column(String)

    proxy_id: Mapped[str | None] = mapped_column(String, ForeignKey("proxies.id"))
    proxy = relationship("Proxy", back_populates="miniverses", lazy="selectin", info=dto_field("private"))

    users_roles = relationship("MiniverseUserRole", back_populates="miniverse", cascade="all, delete-orphan", lazy="selectin", info=dto_field("read-only"))

    mods: Mapped[list[Mod]] = relationship("Mod", back_populates="miniverse", cascade="all, delete-orphan", lazy="selectin", info=dto_field("read-only"))


class MiniverseUserRole(Base):
    __tablename__ = "miniverse_user_roles"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    miniverse_id: Mapped[str] = mapped_column(String, ForeignKey("miniverses.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(Enum(Role))

    user = relationship("User", back_populates="miniverses_roles", info=dto_field("private"))
    miniverse = relationship("Miniverse", back_populates="users_roles", info=dto_field("private"))