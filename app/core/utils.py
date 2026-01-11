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
