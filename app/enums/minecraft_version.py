from enum import Enum

class MinecraftVersionType(str, Enum):
    RELEASE = "release"
    SNAPSHOT = "snapshot"
    ALPHA = "alpha"
    BETA = "beta"
