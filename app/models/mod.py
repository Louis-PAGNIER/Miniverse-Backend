from uuid import uuid4

from litestar.dto import dto_field
from sqlalchemy import String, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core import settings
from app.db import Base


class Mod(Base):
    __tablename__ = "mods"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()),
                                    info=dto_field("read-only"))
    slug: Mapped[str] = mapped_column(String(settings.DATABASE_DEFAULT_STRING_LENGTH), nullable=False)
    version_id: Mapped[str | None] = mapped_column(String(16))
    project_id: Mapped[str | None] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(settings.DATABASE_DEFAULT_STRING_LENGTH))
    icon_url: Mapped[str | None] = mapped_column(Text)
    version_name: Mapped[str | None] = mapped_column(String(settings.DATABASE_DEFAULT_STRING_LENGTH))
    version_number: Mapped[str | None] = mapped_column(String(settings.DATABASE_DEFAULT_STRING_LENGTH))
    file_name: Mapped[str] = mapped_column(String(settings.DATABASE_DEFAULT_STRING_LENGTH), info=dto_field("private"))

    miniverse_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("miniverses.id"),
                                                     info=dto_field("read-only"),
                                                     nullable=False)
    miniverse = relationship("Miniverse", back_populates="mods", lazy="selectin", info=dto_field("private"))
