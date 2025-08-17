import functools
from enum import Enum

@functools.total_ordering
class Role(str, Enum):
    USER = "User"
    MODERATOR = "Moderator"
    ADMIN = "Admin"

    def role_value(self) -> int:
        if self == Role.USER:
            return 1
        elif self == Role.MODERATOR:
            return 2
        elif self == Role.ADMIN:
            return 3
        else:
            raise ValueError(f"Unknown role: {self}")

    def __lt__(self, other: "Role") -> bool:
        if not isinstance(other, Role):
            return NotImplemented
        return self.role_value() < other.role_value()
