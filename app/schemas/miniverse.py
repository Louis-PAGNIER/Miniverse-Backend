from dataclasses import dataclass
from app.enums import MiniverseType


@dataclass
class MiniverseCreate:
    name: str
    type: MiniverseType
    description: str | None
    mc_version: str
    subdomain: str | None
    is_on_lite_proxy: bool

@dataclass
class MiniverseUpdateMCVersion:
    mc_version: str

@dataclass
class AutomaticInstallMod:
    mod_id: str
