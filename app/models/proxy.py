import enum
from uuid import uuid4

from sqlalchemy import String, Enum, Text, Integer, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship

from app.db import Base
from app.enums import Role, ProxyType


class Proxy(Base):
    __tablename__ = "proxies"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String, nullable=False)
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
    type: Mapped[ProxyType] = mapped_column(Enum(ProxyType), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    port: Mapped[int] = mapped_column(Integer, nullable=False)

    miniverses = relationship("Miniverse", back_populates="proxy")
    user_roles = relationship("ProxyUserRole", back_populates="proxy", cascade="all, delete-orphan")


class ProxyUserRole(Base):
    __tablename__ = "proxy_user_roles"

    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), primary_key=True)
    proxy_id: Mapped[str] = mapped_column(String, ForeignKey("proxies.id"), primary_key=True)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False)

    user = relationship("User", back_populates="proxy_roles")
    proxy = relationship("Proxy", back_populates="user_roles")