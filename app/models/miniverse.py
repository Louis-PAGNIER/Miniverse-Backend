from sqlalchemy import String, Text, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from uuid import uuid4

from app.enums import MiniverseType, Role


class Miniverse(Base):
    __tablename__ = "miniverses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[MiniverseType] = mapped_column(Enum(MiniverseType), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
    mc_version: Mapped[str] = mapped_column(String, nullable=False)
    subdomain: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    proxy_id: Mapped[str | None] = mapped_column(String, ForeignKey("proxies.id"), nullable=True)
    proxy = relationship("Proxy", back_populates="miniverses", lazy="selectin")

    users_roles = relationship("MiniverseUserRole", back_populates="miniverse", cascade="all, delete-orphan", lazy="selectin")


class MiniverseUserRole(Base):
    __tablename__ = "miniverse_user_roles"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    miniverse_id: Mapped[str] = mapped_column(String, ForeignKey("miniverses.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)

    user = relationship("User", back_populates="miniverses_roles")
    miniverse = relationship("Miniverse", back_populates="users_roles")