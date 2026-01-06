from dataclasses import dataclass
from datetime import datetime
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
class DownloadFilesRequest:
    paths: list[Path]