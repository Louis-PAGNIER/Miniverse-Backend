from dataclasses import dataclass
from datetime import datetime

from app.enums.minecraft_version import MinecraftVersionType


@dataclass
class MinecraftVersion:
    version: str
    version_type: MinecraftVersionType
    date: datetime
    major: bool

    @staticmethod
    def from_dict(data: dict) -> "MinecraftVersion":
        return MinecraftVersion(
            version=data["version"],
            version_type=MinecraftVersionType(data["version_type"]),
            date=datetime.fromisoformat(data["date"].replace("Z", "+00:00")),
            major=data["major"],
        )