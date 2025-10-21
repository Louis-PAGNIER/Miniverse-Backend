import re

import httpx

from app.schemas.minecraft import MinecraftVersion
from app.services.mods_service import MODRINTH_BASE_URL


# TODO: Add cache on this function
async def get_minecraft_versions() -> list[MinecraftVersion]:
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{MODRINTH_BASE_URL}/tag/game_version")
        response.raise_for_status()
        data = response.json()
        versions = [
            MinecraftVersion.from_dict(v) for v in data
        ]
        return versions


def is_snapshot(game_version: str) -> bool:
    return re.match(r"^\d{2}w\d{2}[a-z]$", game_version) is not None


def is_prerelease(game_version: str) -> bool:
    return re.match(r"^\d{1,2}\.\d{1,2}\.\d{1,2}-(pre|rc)\d*$", game_version) is not None


def is_release(game_version: str) -> bool:
    return re.match(r"^\d{1,2}\.\d{1,2}\.\d{1,2}$", game_version) is not None


def get_version_type(game_version: str) -> str | None:
    if is_snapshot(game_version):
        return "snapshot"
    elif is_prerelease(game_version):
        return "prerelease"
    elif is_release(game_version):
        return "release"
    else:
        return None


def compare_main_versions(major1, minor1, patch1, major2, minor2, patch2) -> int:
    if major1 != major2:
        return (major1 > major2) - (major1 < major2)
    if minor1 != minor2:
        return (minor1 > minor2) - (minor1 < minor2)
    if patch1 != patch2:
        return (patch1 > patch2) - (patch1 < patch2)
    return 0


def compare_prerelease_identifiers(id1: str, id2: str) -> int:
    if id1 == id2:
        return 0

    id1_regex = re.match(r"^(pre|rc)(\d+)$", id1)
    id2_regex = re.match(r"^(pre|rc)(\d+)$", id2)

    id1_rc = id1_regex.group(1) == "rc"
    id2_rc = id2_regex.group(1) == "rc"

    id1_value = id1_regex.group(2)
    id2_value = id2_regex.group(2)

    if id1_rc != id2_rc:
        return (id1_rc > id2_rc) - (id1_rc < id2_rc)
    return int(id1_value) - int(id2_value)


async def compare_by_publish_date(v1: str, v2: str) -> int | None:
    # Fallback comparison by publish date if one of versions is a snapshot because we can't compare them directly
    all_versions = await get_minecraft_versions()
    v1_date = next((v.date for v in all_versions if v.version == v1), None)
    v2_date = next((v.date for v in all_versions if v.version == v2), None)
    if v1_date is None or v2_date is None:
        return None
    return (v1_date > v2_date) - (v1_date < v2_date)


async def compare_versions(v1: str, v2: str) -> int | None:
    """
    Compare two version strings.
    Support many versions formats:
        - Release versions: "1.8.9", "1.21.8", "..."
        - Snapshot versions: "25w37a", "1.20.1-pre2", "1.21-rc1", "..."
    Returns:
        -1 if v1 < v2
         0 if v1 == v2
         1 if v1 > v2
         None if one of the versions is invalid
    """
    if v1 == v2:
        return 0

    v1_type = get_version_type(v1)
    v2_type = get_version_type(v2)

    if v1_type is None or v2_type is None:
        return None

    if v1_type in ["prerelease", "release"] and v2_type in ["prerelease", "release"]:
        v1_parts = re.split(r"[.-]", v1)
        v2_parts = re.split(r"[.-]", v2)

        basic_comparison = compare_main_versions(
            int(v1_parts[0]), int(v1_parts[1]), int(v1_parts[2]),
            int(v2_parts[0]), int(v2_parts[1]), int(v2_parts[2])
        )
        if basic_comparison != 0:
            return basic_comparison

        if v1_type == "release" and v2_type == "prerelease":
            return 1
        if v1_type == "prerelease" and v2_type == "release":
            return -1
        if v1_type == "prerelease" and v2_type == "prerelease":
            return compare_prerelease_identifiers(v1_parts[3], v2_parts[3])
    # TODO: Add local comparison for snapshots if both versions are snapshots
    return await compare_by_publish_date(v1, v2)
