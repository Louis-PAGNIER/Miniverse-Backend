from dataclasses import dataclass

@dataclass
class Player:
    id: str
    name: str
    is_operator: bool

@dataclass
class MSMPPlayer:
    id: str
    name: str

@dataclass
class MSMPPlayerBan:
    reason: str
    expires: str
    source: str
    player: MSMPPlayer

    @staticmethod
    def from_dict(data: dict):
        return MSMPPlayerBan(
            reason=data.get('reason'),
            expires=data.get('expires'),
            source=data.get('source'),
            player=MSMPPlayer(**data['player'])
        )

    def to_dict(self) -> dict:
        return {
            'reason': self.reason,
            'expires': self.expires,
            'source': self.source,
            'player': self.player.__dict__
        }

@dataclass
class MSMPOperator:
    permissionLevel: int
    bypassesPlayerLimit: bool
    player: MSMPPlayer

    @staticmethod
    def from_dict(data: dict):
        return MSMPOperator(
            permissionLevel=data['permissionLevel'],
            bypassesPlayerLimit=data['bypassesPlayerLimit'],
            player=MSMPPlayer(**data['player'])
        )

    def to_dict(self) -> dict:
        return {
            'permissionLevel': self.permissionLevel,
            'bypassesPlayerLimit': self.bypassesPlayerLimit,
            'player': self.player.__dict__
        }