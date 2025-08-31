from uuid import uuid4

from litestar.dto import dto_field
from sqlalchemy import String, Enum, Text, Integer, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db import Base
from app.enums import Role, ProxyType


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()), info=dto_field("read-only"))
    name: Mapped[str] = mapped_column(String)
    container_id: Mapped[str | None] = mapped_column(String)
    type: Mapped[ProxyType] = mapped_column(Enum(ProxyType))
    description: Mapped[str | None] = mapped_column(Text)
    port: Mapped[int] = mapped_column(Integer)

    miniverses = relationship("Miniverse", back_populates="proxy", lazy="selectin", info=dto_field("private"))
    users_roles = relationship("ProxyUserRole", back_populates="proxy", cascade="all, delete-orphan", lazy="selectin", info=dto_field("read-only"))


class ProxyUserRole(Base):
    __tablename__ = "proxy_user_roles"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    proxy_id: Mapped[str] = mapped_column(String, ForeignKey("proxies.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(Enum(Role))

    user = relationship("User", back_populates="proxies_roles", info=dto_field("private"))
    proxy = relationship("Proxy", back_populates="users_roles", info=dto_field("private"))