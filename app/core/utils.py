import random
import string
import zipfile
from copy import copy
from pathlib import Path

import yaml
from litestar.concurrency import sync_to_thread


def quoted_presenter(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style='"')


yaml.add_representer(str, quoted_presenter)


def generate_random_string(length: int) -> str:
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))


def write_yaml_safe(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        yaml.dump(data, f, default_flow_style=False)


def websocket_uri_from_miniverse_id(miniverse_id: str) -> str:
    return f"ws://miniverse-{miniverse_id}:25585"


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