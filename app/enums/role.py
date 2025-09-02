from enum import Enum
from typing import Optional


class Role(str, Enum):
    NONE = "None"
    USER = "User"
    MODERATOR = "Moderator"
    ADMIN = "Admin"

    def role_value(self) -> int:
        return {
            Role.NONE: 0,
            Role.USER: 1,
            Role.MODERATOR: 2,
            Role.ADMIN: 3,
        }[self]

    def __lt__(self, other: Optional["Role"]) -> bool:
        if self.__class__ is other.__class__:
            return self.role_value() < other.role_value()
        if other is None:
            return True
        return NotImplemented

    def __gt__(self, other: Optional["Role"]) -> bool:
        if self.__class__ is other.__class__:
            return self.role_value() > other.role_value()
        if other is None:
            return False
        return NotImplemented

    def __le__(self, other: Optional["Role"]) -> bool:
        if self.__class__ is other.__class__:
            return self.role_value() <= other.role_value()
        if other is None:
            return True
        return NotImplemented

    def __ge__(self, other: Optional["Role"]) -> bool:
        if self.__class__ is other.__class__:
            return self.role_value() >= other.role_value()
        if other is None:
            return False
        return NotImplemented
