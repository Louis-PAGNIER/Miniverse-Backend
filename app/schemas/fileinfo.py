from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


@dataclass
class FileInfo:
    is_folder: bool
    path: str
    name: str
    created: datetime
    updated: datetime
    size: Optional[int]


@dataclass
class FilesRequest:
    paths: list[Path]


@dataclass
class RenameFileRequest:
    path: Path
    new_name: str


class HookType(Enum):
    pre_create = "pre-create"
    post_finish = "post-finish"


@dataclass
class HookRequest:
    Type: HookType
    Event: dict
