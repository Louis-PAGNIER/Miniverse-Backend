from pydantic import BaseModel


class MSMPPlayer(BaseModel):
    id: str
    name: str


class MSMPPlayerBan(BaseModel):
    reason: str
    expires: str
    source: str
    player: MSMPPlayer


class MSMPOperator(BaseModel):
    permissionLevel: int
    bypassesPlayerLimit: bool
    player: MSMPPlayer
