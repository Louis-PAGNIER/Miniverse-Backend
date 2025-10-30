from enum import Enum


class EventType(str, Enum):
    PLAYERS = "players"
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
