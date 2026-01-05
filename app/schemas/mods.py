import enum
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Literal


# TODO: ça exit un décorateur qui fait auto le from_dict ?

class ModrinthProjectType(enum.Enum):
    MOD = "mod"
    MODPACK = "modpack"
    RESOURCEPACK = "resourcepack"
    SHADER = "shader"
    WORLD = "world"


class ModSideSupport(enum.Enum):
    REQUIRED = "required"
    OPTIONAL = "optional"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class ModVersionType(enum.Enum):
    RELEASE = "release"
    BETA = "beta"
    ALPHA = "alpha"


class ModUpdateStatus(enum.Enum):
    ALREADY_UP_TO_DATE = "already_up_to_date"
    UPDATE_AVAILABLE = "update_available"
    NO_COMPATIBLE_VERSIONS = "no_compatible_versions"
    ERROR = "error"


@dataclass
class ModUpdateInfo:
    update_status: ModUpdateStatus
    new_versions_ids: list[str]
    game_versions: list[list[str]]  # list of compatible game versions for each new version


# ================== Modrinth API Schemas ================== #
@dataclass
class ModrinthSearchFacets:
    project_type: ModrinthProjectType = None
    categories: list[str] = None
    versions: list[str] = None
    client_side: ModSideSupport = None
    server_side: ModSideSupport = None


@dataclass
class ModrinthSearchResult:
    project_id: str
    project_type: ModrinthProjectType
    slug: str
    author: str
    title: str
    description: str
    categories: list[str]
    display_categories: list[str]
    versions: list[str]
    downloads: int
    follows: int
    icon_url: str
    date_created: datetime
    date_modified: datetime
    latest_version: str
    license: str
    client_side: ModSideSupport
    server_side: ModSideSupport
    gallery: list
    color: int | None = None
    featured_gallery: list | None = None

    @staticmethod
    def from_dict(data: dict) -> "ModrinthSearchResult":
        return ModrinthSearchResult(
            project_id=data["project_id"],
            project_type=ModrinthProjectType(data["project_type"]),
            slug=data["slug"],
            author=data["author"],
            title=data["title"],
            description=data["description"],
            categories=data["categories"],
            display_categories=data["display_categories"],
            versions=data["versions"],
            downloads=data["downloads"],
            follows=data["follows"],
            icon_url=data["icon_url"],
            date_created=datetime.fromisoformat(data["date_created"].replace("Z", "+00:00")),
            date_modified=datetime.fromisoformat(data["date_modified"].replace("Z", "+00:00")),
            latest_version=data["latest_version"],
            license=data["license"],
            client_side=ModSideSupport(data["client_side"]),
            server_side=ModSideSupport(data["server_side"]),
            gallery=data["gallery"],
            color=data["color"],
            featured_gallery=data.get("featured_gallery"),
        )


@dataclass
class ModrinthGalleryItem:
    url: str
    raw_url: str
    featured: bool
    title: str
    description: str
    created: datetime

    @staticmethod
    def from_dict(data: dict) -> "ModrinthGalleryItem":
        return ModrinthGalleryItem(
            url=data["url"],
            raw_url=data["raw_url"],
            featured=data["featured"],
            title=data["title"],
            description=data["description"],
            created=datetime.fromisoformat(data["created"].replace("Z", "+00:00")),
        )


@dataclass
class ModrinthProject:
    id: str
    slug: str
    title: str
    description: str
    body: str
    categories: list[str]
    client_side: ModSideSupport
    server_side: ModSideSupport
    issues_url: str | None
    source_url: str | None
    wiki_url: str | None
    discord_url: str | None
    color: int | None
    team: str
    published: datetime
    updated: datetime
    followers: int
    project_type: ModrinthProjectType
    downloads: int
    icon_url: str
    versions: list[str]
    game_versions: list[str]
    loaders: list[str]
    gallery: list[ModrinthGalleryItem]

    @staticmethod
    def from_dict(data: dict) -> "ModrinthProject":
        return ModrinthProject(
            id=data["id"],
            slug=data["slug"],
            title=data["title"],
            description=data["description"],
            body=data["body"],
            categories=data["categories"],
            client_side=ModSideSupport(data["client_side"]),
            server_side=ModSideSupport(data["server_side"]),
            issues_url=data.get("issues_url"),
            source_url=data.get("source_url"),
            wiki_url=data.get("wiki_url"),
            discord_url=data.get("discord_url"),
            color=data.get("color"),
            team=data["team"],
            published=datetime.fromisoformat(data["published"].replace("Z", "+00:00")),
            updated=datetime.fromisoformat(data["updated"].replace("Z", "+00:00")),
            followers=data["followers"],
            project_type=ModrinthProjectType(data["project_type"]),
            downloads=data["downloads"],
            icon_url=data["icon_url"],
            versions=data["versions"],
            game_versions=data["game_versions"],
            loaders=data["loaders"],
            gallery=[ModrinthGalleryItem.from_dict(g) for g in data.get("gallery", [])],
        )


@dataclass
class ModrinthSearchResults:
    hits: list[ModrinthSearchResult]
    offset: int
    limit: int
    total_hits: int

    @staticmethod
    def from_dict(data: dict) -> "ModrinthSearchResults":
        return ModrinthSearchResults(
            hits=[ModrinthSearchResult.from_dict(hit) for hit in data["hits"]],
            offset=data["offset"],
            limit=data["limit"],
            total_hits=data["total_hits"],
        )


@dataclass
class ModrinthFileHashes:
    sha1: str
    sha512: str

    @staticmethod
    def from_dict(data: dict) -> "ModrinthFileHashes":
        return ModrinthFileHashes(**data)


@dataclass
class ModrinthProjectFile:
    hashes: ModrinthFileHashes
    url: str
    filename: str
    primary: bool
    size: int
    file_type: Optional[Literal["required-resource-pack", "optional-resource-pack"]] = None

    @staticmethod
    def from_dict(data: dict) -> "ModrinthProjectFile":
        return ModrinthProjectFile(
            hashes=ModrinthFileHashes.from_dict(data["hashes"]),
            url=data["url"],
            filename=data["filename"],
            primary=data["primary"],
            size=data["size"],
            file_type=data.get("file_type"),
        )


@dataclass
class ModrinthProjectVersion:
    id: str
    project_id: str
    author_id: str
    date_published: datetime
    downloads: int
    name: str
    version_number: str
    changelog: str
    game_versions: list[str]
    version_type: ModVersionType
    loaders: list[str]
    featured: bool
    status: str
    requested_status: str
    files: list[ModrinthProjectFile]
    dependencies: list[str] | None = None

    @staticmethod
    def from_dict(data: dict) -> "ModrinthProjectVersion":
        return ModrinthProjectVersion(
            id=data["id"],
            project_id=data["project_id"],
            author_id=data["author_id"],
            date_published=datetime.fromisoformat(
                data["date_published"].replace("Z", "+00:00")
            ),
            downloads=data["downloads"],
            name=data["name"],
            version_number=data["version_number"],
            changelog=data["changelog"],
            game_versions=data["game_versions"],
            version_type=ModVersionType(data["version_type"]),
            loaders=data["loaders"],
            featured=data["featured"],
            status=data["status"],
            requested_status=data["requested_status"],
            files=[ModrinthProjectFile.from_dict(f) for f in data["files"]],
            dependencies=data.get("dependencies"),
        )
