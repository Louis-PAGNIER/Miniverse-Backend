from pathlib import Path

from litestar import Controller, get, post, Response, MediaType
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException, NotFoundException
from sqlalchemy.ext.asyncio import AsyncSession

from app import get_db_session
from app.core import settings
from app.enums import Role
from app.models import User
from app.schemas.fileinfo import FileInfo, FilesRequest, RenameFileRequest, HookRequest, HookType
from app.services.auth_service import get_current_user
from app.services.files_service import list_miniverse_files, delete_miniverse_files, copy_miniverse_files, \
    transform_safe_miniverse_files, download_files, upload_miniverse_file, extract_miniverse_archive, rename_file, \
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

        paths: list[Path] = [Path(path) for path in
                             paths.split(",")]  # TODO files can have "," -> quote all path to fix this issue
        safe_paths = transform_safe_miniverse_files(miniverse, paths)

        if len(safe_paths) <= 0:
            raise NotFoundException("Dossier vide")

        return download_files(safe_paths)

    @post("/tus-hooks")
    async def confirm_upload(
            self,
            current_user: User,
            data: HookRequest,
            db: AsyncSession
    ) -> Response | None:
        # 1. AUTHENTICATION (pre-create)
        if data.Type == HookType.pre_create:
            # Tus forwards headers from the client.
            # The client must send 'Upload-Metadata: token=xyz' or standard headers.
            meta = data.Event["Upload"]["MetaData"]
            miniverse_id = meta["miniverseId"]
            if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
                return Response(content={
                    'HTTPResponse': {
                        'StatusCode': 401,
                        'Headers': {},
                        'Body': "You are not authorized to upload files in this miniverse"
                    },
                    'RejectUpload': True,
                }, media_type=MediaType.JSON)

            print(f"User authorized. Starting upload for {meta["filename"]}")
            return Response(content={
                'HTTPResponse': {
                    'StatusCode': 204,
                },
                'RejectUpload': False,
            }, media_type=MediaType.JSON)

        # 2. COMPLETION (post-finish)
        if data.Type == HookType.post_finish:
            file_id = data.Event["Upload"]["ID"]
            # The file is now fully on disk at ./data/{file_id}
            print(f"Upload complete! File ID: {file_id}")

            # Trigger your processing logic here (e.g. database update)
            meta = data.Event["Upload"]["MetaData"]
            miniverse_id = meta['miniverseId']

            # Check user permission a second time before adding file
            if current_user.get_miniverse_role(miniverse_id) < Role.MODERATOR:
                # Remove uploaded file and related .info
                (settings.DATA_PATH / "uploads" / file_id).unlink()
                (settings.DATA_PATH / "uploads" / (file_id + '.info')).unlink()
                return None

            miniverse = await get_miniverse(miniverse_id, db)

            filename = meta["filename"]
            destination = Path(meta["destination"])
            await upload_miniverse_file(miniverse, file_id, filename, destination)

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
