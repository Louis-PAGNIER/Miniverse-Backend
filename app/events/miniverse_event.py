import json
from dataclasses import dataclass

from app.core import channels_plugin, settings
from app.enums.event_type import EventType
from app.models import MiniverseUserRole
from app.schemas import Player, MSMPPlayerBan


@dataclass
class MiniverseEvent:
    type: EventType
    miniverse_id: str
    data: dict | list
    updated_user_ids: list[str] | None = None

    @staticmethod
    def from_bytes(data: bytes) -> "MiniverseEvent":
        event_dict = json.loads(data)
        return MiniverseEvent(
            type=EventType(event_dict["type"]),
            miniverse_id=event_dict["miniverse_id"],
            data=event_dict.get("data"),
            updated_user_ids=event_dict.get("updated_user_ids"))


def user_list_from_user_role_list(user_roles: list[MiniverseUserRole]) -> list[str]:
    return list(map(lambda user_role: user_role.user_id, user_roles))


def publish_miniverse_players_event(miniverse_id: str, players: list[Player]) -> None:
    channels_plugin.publish(MiniverseEvent(
        type=EventType.PLAYERS,
        miniverse_id=miniverse_id,
        data=players),
        settings.REDIS_CHANNEL_NAME)


def publish_miniverse_ban_player_event(miniverse_id: str, bans: list[MSMPPlayerBan]) -> None:
    channels_plugin.publish(MiniverseEvent(
        type=EventType.PLAYER_BAN,
        miniverse_id=miniverse_id,
        data=bans),
        settings.REDIS_CHANNEL_NAME)


def publish_miniverse_created_event(miniverse_id: str, updated_user_ids: list[str]) -> None:
    channels_plugin.publish(MiniverseEvent(
        type=EventType.CREATED,
        miniverse_id=miniverse_id,
        data={},
        updated_user_ids=updated_user_ids),
        settings.REDIS_CHANNEL_NAME)


def publish_miniverse_deleted_event(miniverse_id: str, updated_user_ids: list[str]) -> None:
    channels_plugin.publish(MiniverseEvent(
        type=EventType.DELETED,
        miniverse_id=miniverse_id,
        data={},
        updated_user_ids=updated_user_ids),
        settings.REDIS_CHANNEL_NAME)


def publish_miniverse_updated_event(miniverse_id: str, updated_user_ids: list[str] | None = None) -> None:
    channels_plugin.publish(MiniverseEvent(
        type=EventType.UPDATED,
        miniverse_id=miniverse_id,
        data={},
        updated_user_ids=updated_user_ids),
        settings.REDIS_CHANNEL_NAME)
