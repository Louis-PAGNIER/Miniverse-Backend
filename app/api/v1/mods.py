from typing import Annotated

from litestar import get, Controller
from litestar.di import Provide
from litestar.params import Parameter

from app.db.session import get_db_session
from app.schemas import ModrinthSearchResults, ModrinthSearchFacets, ModrinthProjectType, ModrinthProjectVersion, \
    ModrinthProject
from app.services.mods_service import search_modrinth_projects, get_project_details, list_project_versions, \
    get_version_details


class ModsController(Controller):
    path = "/mods"
    tags = ["Mods"]
    dependencies = {"db": Provide(get_db_session)}

    @get("/search")
    async def search_mods(self, query_search: Annotated[str, Parameter(query="query")], limit: int = 20, offset: int = 0) -> ModrinthSearchResults:
        return await search_modrinth_projects(
            query_search,
            facets=ModrinthSearchFacets(
                project_type=ModrinthProjectType.MOD,
            ),
            limit=limit,
            offset=offset
        )

    @get("{project_id:str}/details")
    async def get_mod_details(self, project_id: str) -> ModrinthProject:
        return await get_project_details(project_id)

    @get("{version_id:str}/details/version")
    async def get_mod_version_details(self, version_id: str) -> ModrinthProjectVersion:
        return await get_version_details(version_id)

    @get("{project_id:str}/versions")
    async def list_mod_versions(self, project_id: str) -> list[ModrinthProjectVersion]:
        return await list_project_versions(project_id)