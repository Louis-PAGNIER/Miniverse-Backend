import json
import uuid
from pathlib import Path
from typing import Annotated

from litestar import Controller, get, post
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotAuthorizedException
from litestar.params import Body
from litestar.response import File, Stream
from sqlalchemy.ext.asyncio import AsyncSession

from app import get_db_session
from app.core import root_store
from app.enums import Role
from app.models import User
from app.schemas.fileinfo import FileInfo, FilesRequest
from app.services.auth_service import get_current_user
from app.services.files_service import list_miniverse_files, delete_miniverse_files, copy_miniverse_files, \
    transform_safe_miniverse_files, download_files, upload_miniverse_files, extract_miniverse_archive
from app.services.miniverse_service import get_miniverse

download_tokens_store = root_store.with_namespace("download-tokens")

class FilesController(Controller):
    path = "/api/files"
    tags = ["Files"]
    dependencies = {
        "db": Provide(get_db_session),
        "current_user": Provide(get_current_user),
    }

    @get("/{miniverse_id:str}")
    async def list_miniverse_files(self, current_user: User, miniverse_id: str, db: AsyncSession,
                                   path: Path = Path("/")) -> list[FileInfo]:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to view files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return list_miniverse_files(miniverse, path)

    @post("/{miniverse_id:str}/delete")
    async def delete_miniverse_files(self, current_user: User, miniverse_id: str, db: AsyncSession,
                                     data: FilesRequest) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to delete files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return delete_miniverse_files(miniverse, data.paths)

    @post("/{miniverse_id:str}/copy")
    async def copy_miniverse_files(self, current_user: User, miniverse_id: str, db: AsyncSession, data: FilesRequest,
                                   destination: Path) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to copy files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return copy_miniverse_files(miniverse, data.paths, destination)

    @post("/{miniverse_id:str}/download-token")
    async def create_download_miniverse_files_token(
            self,
            current_user: User,
            miniverse_id: str,
            data: FilesRequest,
            db: AsyncSession,
    ) -> str:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to view files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)
        safe_paths = transform_safe_miniverse_files(miniverse, data.paths)

        token = uuid.uuid4().hex
        await download_tokens_store.set(token, json.dumps([str(p) for p in safe_paths]))

        return token

    @get("/download/{token:str}", exclude_from_auth=True)
    async def download_files(self, token: str) -> File | Stream:
        data = await download_tokens_store.get(token)
        if data is None:
            raise ValueError("Invalid token")

        paths: list[Path] = [Path(p) for p in json.loads(data)]
        return download_files(paths)

    @post("/{miniverse_id:str}/upload", request_max_body_size=50 * (1024 ** 3))
    async def upload_miniverse_files(
            self,
            current_user: User,
            miniverse_id: str,
            db: AsyncSession,
            data: Annotated[list[UploadFile], Body(media_type=RequestEncodingType.MULTI_PART)],
            destination: Path = Path("/"),
    ) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to upload files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return await upload_miniverse_files(miniverse, data, destination)

    @post("/{miniverse_id:str}/extract")
    async def extract_miniverse_archive(
            self,
            current_user: User,
            miniverse_id: str,
            db: AsyncSession,
            path: Path = Path("/"),
    ) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to upload files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return await extract_miniverse_archive(miniverse, path)