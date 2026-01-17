from enum import Enum


class EventType(str, Enum):
    PLAYERS = "players"
    PLAYER_BAN = "player-ban"
    CREATED = "created"
    DELETED = "deleted"
    UPDATED = "updated"
