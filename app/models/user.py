from litestar.dto import dto_field
from sqlalchemy import String, Enum, ForeignKey, Boolean
from sqlalchemy.orm import relationship, mapped_column, Mapped

from app.core import settings
from app.db import Base
from app.enums import Role


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, info=dto_field("read-only"))
    is_active: Mapped[bool] = mapped_column(Boolean, index=True, nullable=False, default=False,
                                            info=dto_field("private"))
    username: Mapped[str] = mapped_column(String(settings.DATABASE_DEFAULT_STRING_LENGTH), unique=True, index=True,
                                          nullable=False)
    role: Mapped[Role] = mapped_column(Enum(Role), nullable=False, default=Role.USER)

    miniverses_roles: Mapped[list["MiniverseUserRole"]] = relationship("MiniverseUserRole", back_populates="user",
                                                                       cascade="all, delete-orphan", lazy="selectin",
                                                                       info=dto_field("private"))

    @property
    def is_admin(self) -> bool:
        return self.role >= Role.ADMIN

    @property
    def is_moderator(self) -> bool:
        return self.role >= Role.MODERATOR

    def get_miniverse_role(self, miniverse_id: str) -> Role:
        for role in self.miniverses_roles:
            if role.miniverse_id == miniverse_id:
                return role.role
        return Role.NONE


class MiniverseUserRole(Base):
    __tablename__ = "miniverse_user_roles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"),
                                         info=dto_field("read-only"),
                                         primary_key=True)
    miniverse_id: Mapped[str] = mapped_column(String(36), ForeignKey("miniverses.id", ondelete="CASCADE"),
                                              info=dto_field("read-only"),
                                              primary_key=True)
    role: Mapped[Role] = mapped_column(Enum(Role))

    user = relationship("User", back_populates="miniverses_roles", info=dto_field("private"), lazy="selectin")
    miniverse = relationship("Miniverse", back_populates="users_roles", info=dto_field("private"), lazy="selectin")
