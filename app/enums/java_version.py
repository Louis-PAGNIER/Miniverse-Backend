from enum import Enum


class JavaVersion(str, Enum):
    JAVA25 = "java25"
    JAVA21 = "java21"
    JAVA17 = "java17"
    JAVA11 = "java11"
    JAVA8 = "java8"
