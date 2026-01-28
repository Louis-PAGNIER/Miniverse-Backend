import shutil
import zipfile
import zlib
from copy import copy
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import quote

import zipstream
from litestar import Response
from litestar.concurrency import sync_to_thread

from app.core import root_store, settings
from app.models import Miniverse
from app.schemas.fileinfo import FileInfo, NginxUploadData
from app.services.miniverse_service import get_miniverse_path

download_tokens_store = root_store.with_namespace("download-tokens")


def safe_user_path(root: Path, user_relative_path: Path) -> Path:
    base = root.resolve()
    user_relative_path = Path("./" + str(user_relative_path))
    target = (base / user_relative_path).resolve(strict=False)

    if not target.is_relative_to(base):
        raise ValueError("Specified path is invalid")

    return target


def change_path_name_if_exists(path: Path) -> Path:
    parent = path.parent
    new_path = copy(path)

    i = 1
    while new_path.exists():
        i += 1
        if path.is_dir():
            new_path = parent / f"{path.name} ({i})"
        else:
            new_path = parent / f"{path.stem} ({i}){path.suffix}"

    return new_path


def get_zip_roots(z: zipfile.ZipFile) -> set[str]:
    roots: set[str] = set()

    for info in z.infolist():
        if not info.filename:
            continue

        parts = Path(info.filename).parts
        if parts:
            roots.add(parts[0])

    return roots


async def _extract_zip(
        archive_path: Path,
        extract_dir: Path,
):
    def extract():
        with zipfile.ZipFile(archive_path) as z:
            roots = get_zip_roots(z)

            if len(roots) == 1:
                container_name = next(iter(roots))
            else:
                container_name = archive_path.stem

            container_dir = change_path_name_if_exists(
                safe_user_path(extract_dir, Path(container_name))
            )

            container_dir.mkdir(parents=True, exist_ok=True)

            for member in z.infolist():
                if member.is_dir():
                    continue

                member_path = Path(member.filename)

                if len(roots) == 1:
                    member_path = Path(*member_path.parts[1:])

                target = safe_user_path(container_dir, member_path)
                target.parent.mkdir(parents=True, exist_ok=True)

                with z.open(member) as src, target.open("wb") as dst:
                    while chunk := src.read(1024 * 1024):
                        dst.write(chunk)

    await sync_to_thread(extract)


def list_miniverse_files(miniverse: Miniverse, user_path: Path) -> list[FileInfo]:
    miniverse_data_path = get_miniverse_path(miniverse.id) / 'data'
    safe_path = safe_user_path(miniverse_data_path, user_path)

    files = []
    for path in Path(safe_path).glob("*"):
        stats = path.stat()

        # TODO: Created is not really creation time on UNIX system, we should probably change this in the future
        created_at = datetime.fromtimestamp(stats.st_ctime)
        modified_at = datetime.fromtimestamp(stats.st_mtime)
        is_dir = path.is_dir()
        size = stats.st_size if not is_dir else None

        file = FileInfo(
            is_folder=is_dir,
            path=str(path.relative_to(miniverse_data_path).as_posix()),
            name=path.name,
            created=created_at,
            updated=modified_at,
            size=size,
        )
        files.append(file)

    return files


def delete_miniverse_files(miniverse: Miniverse, paths: list[Path]):
    miniverse_data_path = get_miniverse_path(miniverse.id) / 'data'
    safe_paths = [safe_user_path(miniverse_data_path, path) for path in paths]
    for safe_path in safe_paths:
        if safe_path.exists():
            if safe_path.is_dir():
                shutil.rmtree(safe_path)
            else:
                safe_path.unlink()


def copy_miniverse_files(miniverse: Miniverse, paths: list[Path], destination_path: Path):
    miniverse_data_path = get_miniverse_path(miniverse.id) / 'data'
    safe_paths = [safe_user_path(miniverse_data_path, path) for path in paths]
    safe_destination_path = safe_user_path(miniverse_data_path, destination_path)

    for src in safe_paths:
        if not src.exists():
            continue

        dst = change_path_name_if_exists(safe_destination_path / src.name)

        if src.is_dir():
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)


def transform_safe_miniverse_files(miniverse: Miniverse, paths: list[Path]):
    miniverse_data_path = get_miniverse_path(miniverse.id) / "data"
    return [safe_user_path(miniverse_data_path, p) for p in paths]


def compute_crc32(file_path):
    crc = 0
    # We read in 1MB chunks for a good balance between speed and RAM
    chunk_size = 1024 * 1024

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            # zlib.crc32(data, starting_crc) allows incremental updates
            crc = zlib.crc32(data, crc)

    # Convert to unsigned 32-bit hex string (8 characters)
    return format(crc & 0xFFFFFFFF, '08x')


def add_to_manifest(manifest: list[Any], parent: Path, path: Path):
    stat = path.stat()
    nginx_path = path.relative_to(settings.DATA_PATH)
    zip_path = path.relative_to(parent)

    crc = "-"
    # TODO test if this lines below helps download speed / download retries
    # if stat.st_size >= 100_000_000:
    #     crc = compute_crc32(path)

    manifest.append(f"{crc} {stat.st_size} /internal/{quote(nginx_path.as_posix(), safe='/')} {zip_path}")


def download_files(paths: list[Path]) -> Response:
    if len(paths) == 1:
        if paths[0].is_file():
            internal_path = f"/internal/{paths[0].relative_to(settings.DATA_PATH).as_posix()}"
            response = Response(content="")
            response.headers["X-Accel-Redirect"] = internal_path
            response.headers["Content-Type"] = "application/octet-stream"
            response.headers["Content-Disposition"] = f'attachment; filename="{paths[0].name}"'
            return response

    manifest = []
    for path in paths:
        parent = path.parent
        if path.is_file():
            add_to_manifest(manifest, parent, path)
        elif path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    add_to_manifest(manifest, parent, file)

    response = Response(content="\n".join(manifest) + "\n")
    response.headers["X-Archive-Files"] = "zip"  # Trigger mod_zip
    response.headers["Content-Type"] = "application/zip"
    response.headers["Content-Disposition"] = 'attachment; filename="archive.zip"'
    return response


async def upload_miniverse_files(miniverse: Miniverse, files: NginxUploadData, destination: Path):
    base_path = get_miniverse_path(miniverse.id) / "data"
    dest_path = safe_user_path(base_path, destination)

    if dest_path.is_file():
        raise ValueError("Destination must be a directory")

    dest_path.mkdir(parents=True, exist_ok=True)

    uploads = zip(files.name, files.path)
    for upload in uploads:
        filename = upload[0]
        tmp_path = upload[1]
        relative_path = Path(filename)
        target = safe_user_path(dest_path, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target = change_path_name_if_exists(target)

        tmp_path = settings.DATA_PATH.parent / Path("./" + str(tmp_path))
        tmp_path.rename(target)


async def extract_miniverse_archive(miniverse: Miniverse, path: Path):
    base_path = get_miniverse_path(miniverse.id) / "data"
    file_to_extract = safe_user_path(base_path, path)

    if not file_to_extract.is_file():
        raise ValueError(f"File {file_to_extract} does not exist")

    extract_dir = file_to_extract.parent

    if file_to_extract.suffix.lower() == ".zip":
        await _extract_zip(file_to_extract, extract_dir)
    else:
        raise ValueError("Unsupported archive format")


async def compress_miniverse_files(miniverse: Miniverse, paths: list[Path]):
    miniverse_data_path = get_miniverse_path(miniverse.id) / "data"
    files_to_compress = [safe_user_path(miniverse_data_path, p) for p in paths]

    parents = set()
    for file in files_to_compress:
        parents.add(file.parent)

    if len(parents) != 1:
        raise ValueError("Files to compress must have same parent")

    destination_name = files_to_compress[0].name + ".zip" if len(files_to_compress) == 1 else "Archive.zip"
    destination = change_path_name_if_exists(files_to_compress[0].parent / destination_name)

    z = zipstream.ZipFile(compression=zipstream.ZIP_DEFLATED)

    for path in paths:
        parent = path.parent
        if path.is_file():
            z.write(path, arcname=path.relative_to(parent))
        elif path.is_dir():
            for file in path.rglob("*"):
                if file.is_file():
                    z.write(file, arcname=file.relative_to(parent))

    with open(destination, 'wb') as f:
        for data in z:
            f.write(data)


def rename_file(miniverse: Miniverse, path: Path, new_name: str):
    base_path = get_miniverse_path(miniverse.id) / "data"
    file_to_rename = safe_user_path(base_path, path)

    new_path = path.with_name(new_name)
    new_path_safe = safe_user_path(base_path, new_path)
    if new_path_safe.exists():
        raise ValueError(f"File {new_path_safe} already exists")

    file_to_rename.rename(new_path_safe)
