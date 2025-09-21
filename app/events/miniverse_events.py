from app.core import channels_plugin
from app.schemas import Player


def publish_miniverse_players_event(miniverse_id: str, players: list[Player]) -> None:
    channels_plugin.publish({
        "type": "players",
        "miniverse-id": miniverse_id,
        "data": players
    }, "miniverse-updates")


def publish_miniverse_created_event(miniverse_id: str) -> None:
    channels_plugin.publish({
        "type": "created",
        "miniverse-id": miniverse_id,
        "data": {}
    }, "miniverse-updates")


def publish_miniverse_deleted_event(miniverse_id: str) -> None:
    channels_plugin.publish({
        "type": "deleted",
        "miniverse-id": miniverse_id,
        "data": {}
    }, "miniverse-updates")


def publish_miniverse_updated_event(miniverse_id: str) -> None:
    channels_plugin.publish({
        "type": "updated",
        "miniverse-id": miniverse_id,
        "data": {}
    }, "miniverse-updates")