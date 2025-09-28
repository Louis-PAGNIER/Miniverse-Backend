from litestar.dto import dto_field
from sqlalchemy import String, Text, Enum, ForeignKey, Boolean
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
    container_id: Mapped[str | None] = mapped_column(String, info=dto_field("private"))
    mc_version: Mapped[str] = mapped_column(String)
    subdomain: Mapped[str] = mapped_column(String)
    is_on_lite_proxy: Mapped[bool] = mapped_column(Boolean)
    started: Mapped[bool] = mapped_column(Boolean, default=False, info=dto_field("read-only"))
    management_server_secret: Mapped[str | None] = mapped_column(String(length=40), info=dto_field("private"))

    users_roles = relationship("MiniverseUserRole", back_populates="miniverse", cascade="all, delete-orphan", lazy="selectin", info=dto_field("read-only"))
    mods: Mapped[list[Mod]] = relationship("Mod", back_populates="miniverse", cascade="all, delete-orphan", lazy="selectin", info=dto_field("read-only"))
