import re
from dataclasses import dataclass

import httpx

from app.schemas.minecraft import MinecraftVersion
from app.services.mods_service import MODRINTH_BASE_URL

OLD_RELEASE_FORMAT = re.compile(r"^(?P<major>\d{1,2})\.(?P<minor>\d{1,2})(?:\.(?P<patch>\d{1,2}))?$")
NEW_RELEASE_FORMAT = re.compile(r"^(?P<major>\d{2})\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?$")

OLD_SNAPSHOT_FORMAT = re.compile(r"^(?P<year>\d{2})w(?P<week>\d{2})(?P<type_version>[a-z])$")
NEW_SNAPSHOT_FORMAT = re.compile(r"^(?P<major>\d{2})\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?-(?P<suffix>snapshot)-(?P<type_version>\d+)$")

OLD_PRERELEASE_FORMAT = re.compile(r"^(?P<major>\d{1,2})\.(?P<minor>\d{1,2})(?:\.(?P<patch>\d{1,2}))?-(?P<suffix>pre|rc)(?P<type_version>\d+)$")
# TODO: Currently not documented, will have to wait for a first MC prerelease
NEW_PRERELEASE_FORMAT = re.compile(r"^(?P<major>\d{2})\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?-(?P<suffix>pre|rc)-(?P<type_version>\d+)$")

@dataclass
class ParsedMinecraftVersion:
    value: str
    type: str
    system: str
    major: int
    minor: int
    patch: int
    type_version: int = 0
    suffix: str | None = None

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


def parse_version(version: str) -> ParsedMinecraftVersion | None:
    if (match := re.match(OLD_RELEASE_FORMAT, version)) is not None:
        return ParsedMinecraftVersion(
            match.group(0),
            'release',
            'old',
            int(match.group('major')),
            int(match.group('minor')),
            int(match.group('patch')),
        )
    if (match := re.match(NEW_RELEASE_FORMAT, version)) is not None:
        return ParsedMinecraftVersion(
            match.group(0),
            'release',
            'new',
            int(match.group('major')),
            int(match.group('minor')),
            int(match.group('patch')),
        )
    if (match := re.match(OLD_PRERELEASE_FORMAT, version)) is not None:
        return ParsedMinecraftVersion(
            match.group(0),
            'prerelease',
            'old',
            int(match.group('major')),
            int(match.group('minor')),
            int(match.group('patch')),
            int(match.group('type_version')),
            match.group('suffix'),
        )
    if (match := re.match(NEW_PRERELEASE_FORMAT, version)) is not None:
        return ParsedMinecraftVersion(
            match.group(0),
            'prerelease',
            'new',
            int(match.group('major')),
            int(match.group('minor')),
            int(match.group('patch')),
            int(match.group('type_version')),
            match.group('suffix'),
        )
    if (match := re.match(OLD_SNAPSHOT_FORMAT, version)) is not None:
        return ParsedMinecraftVersion(
            match.group(0),
            'snapshot',
            'old',
            int(match.group('year')),
            int(match.group('week')),
            0,
            match.group('type_version'),
        )
    if (match := re.match(NEW_SNAPSHOT_FORMAT, version)) is not None:
        return ParsedMinecraftVersion(
            match.group(0),
            'snapshot',
            'new',
            int(match.group('major')),
            int(match.group('minor')),
            int(match.group('patch')),
            int(match.group('type_version')),
            match.group('suffix'),
        )
    return None


def compare_main_versions(major1, minor1, patch1, major2, minor2, patch2, type_version1 = 0, type_version2 = 0) -> int:
    if major1 != major2:
        return (major1 > major2) - (major1 < major2)
    if minor1 != minor2:
        return (minor1 > minor2) - (minor1 < minor2)
    if patch1 != patch2:
        return (patch1 > patch2) - (patch1 < patch2)
    if type_version1 != type_version2:
        return (type_version1 > type_version2) - (type_version1 < type_version2)
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

    v1_parsed = parse_version(v1)
    v2_parsed = parse_version(v2)

    if v2_parsed is None or v2_parsed is None:
        return None

    if v1_parsed.type == "snapshot" and v1_parsed.system == "old" \
            or v2_parsed.type == "snapshot" and v2_parsed.system == "old":
        return await compare_by_publish_date(v1, v2)

    basic_comparison = compare_main_versions(
        v1_parsed.major, v1_parsed.minor, v1_parsed.patch,
        v2_parsed.major, v2_parsed.minor, v2_parsed.patch,
    )
    if basic_comparison != 0:
        return basic_comparison

    if v1_parsed.type == "release" and v2_parsed.type == "prerelease":
        return 1
    if v1_parsed.type == "prerelease" and v2_parsed.type == "release":
        return -1
    if v1_parsed.type == "prerelease" and v2_parsed.type == "prerelease":
        return compare_prerelease_identifiers(v1_parsed.suffix, v2_parsed.suffix)

    return await compare_by_publish_date(v1, v2)
