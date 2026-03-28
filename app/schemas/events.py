from pydantic import BaseModel
from typing_extensions import Literal

from app.enums.event_type import EventType
from app.schemas import MSMPPlayer, MSMPOperator, MSMPPlayerBan, MiniverseSchema


class SyncEventItem(BaseModel):
    miniverse: MiniverseSchema
    players: list[MSMPPlayer]
    seen_players: list[MSMPPlayer]
    operators: list[MSMPOperator]
    banned_players: list[MSMPPlayerBan]


class SyncEvent(BaseModel):
    type: Literal[EventType.SYNC] = EventType.SYNC
    data: list[SyncEventItem]
