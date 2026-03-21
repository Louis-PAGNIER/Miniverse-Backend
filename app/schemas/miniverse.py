from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.enums import MiniverseType


class MiniverseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    type: MiniverseType
    description: Optional[str] = None
    mc_version: str
    subdomain: str
    is_on_lite_proxy: bool
    allow_bedrock: bool
    started: bool


class MiniverseCreate(BaseModel):
    name: str
    type: MiniverseType
    description: str | None
    mc_version: str
    subdomain: str | None
    is_on_lite_proxy: bool


class MiniverseUpdateMCVersion(BaseModel):
    mc_version: str


class AutomaticInstallMod(BaseModel):
    mod_id: str
