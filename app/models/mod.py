from litestar.dto import dto_field
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from uuid import uuid4


class Mod(Base):
    __tablename__ = "mods"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid4()), info=dto_field("read-only"))
    slug: Mapped[str] = mapped_column(String, nullable=False)
    version_id: Mapped[str | None] = mapped_column(String)
    project_id: Mapped[str | None] = mapped_column(String)
    title: Mapped[str] = mapped_column(String)
    icon_url: Mapped[str | None] = mapped_column(String)
    version_name: Mapped[str | None] = mapped_column(String)
    version_number: Mapped[str | None] = mapped_column(String)
    file_name: Mapped[str] = mapped_column(String, info=dto_field("private"))

    miniverse_id: Mapped[str | None] = mapped_column(String, ForeignKey("miniverses.id"), nullable=False)
    miniverse = relationship("Miniverse", back_populates="mods", lazy="selectin")
