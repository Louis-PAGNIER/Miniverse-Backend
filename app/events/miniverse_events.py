from app.core import channels_plugin, settings
from app.schemas import Player


# TODO: Create Event object class that can be passed in publish function
def publish_miniverse_players_event(miniverse_id: str, players: list[Player]) -> None:
    channels_plugin.publish({
        "type": "players",
        "miniverse-id": miniverse_id,
        "data": players
    }, settings.REDIS_CHANNEL_NAME)


def publish_miniverse_created_event(miniverse_id: str) -> None:
    channels_plugin.publish({
        "type": "created",
        "miniverse-id": miniverse_id,
        "data": {}
    }, settings.REDIS_CHANNEL_NAME)


def publish_miniverse_deleted_event(miniverse_id: str) -> None:
    channels_plugin.publish({
        "type": "deleted",
        "miniverse-id": miniverse_id,
        "data": {}
    }, settings.REDIS_CHANNEL_NAME)


def publish_miniverse_updated_event(miniverse_id: str) -> None:
    channels_plugin.publish({
        "type": "updated",
        "miniverse-id": miniverse_id,
        "data": {}
    }, settings.REDIS_CHANNEL_NAME)
