from litestar import Controller, get
from litestar.exceptions import NotFoundException

from app.schemas.minecraft import MinecraftVersion
from app.services.minecraft_service import get_minecraft_versions

class MinecraftController(Controller):
    path = "/api/minecraft"
    tags = ["Minecraft"]

    @get('/versions')
    async def list_minecraft_versions(self, min_version: str = None) -> list[MinecraftVersion]:
        all_versions = await get_minecraft_versions()
        if min_version is None:
            return all_versions
        min_version = min_version.lower().strip()
        min_version_index = next((i for i, v in enumerate(all_versions) if v.version == min_version), None)
        if min_version_index is not None:
            return all_versions[:min_version_index + 1]

        raise NotFoundException(f"Minecraft version '{min_version}' not found")
