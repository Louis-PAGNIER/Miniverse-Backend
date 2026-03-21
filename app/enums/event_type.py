from enum import Enum


class EventType(str, Enum):
    SYNC = "sync"

    PLAYERS = "minecraft:players"
    OPERATORS = "minecraft:operators"
    PLAYER_BAN = "minecraft:bans"

    CREATED = "miniverse:created"
    DELETED = "miniverse:deleted"
    UPDATED = "miniverse:updated"
