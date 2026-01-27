from pathlib import Path
from typing import Annotated

from litestar import Controller, get, post, Response
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import RequestEncodingType
from litestar.exceptions import NotAuthorizedException, NotFoundException
from litestar.params import Body
from sqlalchemy.ext.asyncio import AsyncSession

from app import get_db_session
from app.enums import Role
from app.models import User
from app.schemas.fileinfo import FileInfo, FilesRequest, RenameFileRequest
from app.services.auth_service import get_current_user
from app.services.files_service import list_miniverse_files, delete_miniverse_files, copy_miniverse_files, \
    transform_safe_miniverse_files, download_files, upload_miniverse_files, extract_miniverse_archive, rename_file, \
    compress_miniverse_files
from app.services.miniverse_service import get_miniverse


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

    @get("/{miniverse_id:str}/download")
    async def download_files(
            self,
            paths: str,
            current_user: User,
            miniverse_id: str,
            db: AsyncSession
    ) -> Response:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to view files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        paths: list[Path] = [Path(path) for path in paths.split(",")]
        safe_paths = transform_safe_miniverse_files(miniverse, paths)

        if len(safe_paths) <= 0:
            raise NotFoundException("Dossier vide")

        return download_files(safe_paths)

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

    @post("/{miniverse_id:str}/compress")
    async def compress_miniverse_files(
            self,
            current_user: User,
            miniverse_id: str,
            data: FilesRequest,
            db: AsyncSession
    ) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to compress files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        return await compress_miniverse_files(miniverse, data.paths)

    @post("/{miniverse_id:str}/rename")
    async def rename_miniverse_file(self, current_user: User, miniverse_id: str, db: AsyncSession,
                                    data: RenameFileRequest) -> None:
        if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
            raise NotAuthorizedException("You are not authorized to rename files in this miniverse")

        miniverse = await get_miniverse(miniverse_id, db)

        rename_file(miniverse, data.path, data.new_name)
