from dataclasses import dataclass

from app.enums import Role


@dataclass
class RoleSchema:
    role: Role