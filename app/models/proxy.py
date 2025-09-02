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

    miniverses = relationship("Miniverse", back_populates="proxy", lazy="selectin", info=dto_field("private"), passive_deletes=True)
    users_roles = relationship("ProxyUserRole", back_populates="proxy", cascade="all, delete-orphan", lazy="selectin", info=dto_field("read-only"))
