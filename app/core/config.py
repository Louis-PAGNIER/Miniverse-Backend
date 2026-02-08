from pathlib import Path

from pydantic_settings import BaseSettings


# Some settings have default values
class Settings(BaseSettings):
    PROXY_SOCKS: str | None = None
    PROXY_SECRET: str
    HOST_DATA_PATH: Path
    DATA_PATH: Path = "/app/data"
    SQLALCHEMY_DATABASE_PATH: str = "mysql/miniverse_db"
    SQLALCHEMY_DATABASE_PASSWORD: str
    DATABASE_DEFAULT_STRING_LENGTH: int = 128
    DOCKER_NETWORK_NAME: str = "miniverse-net"
    REDIS_HOST_NAME: str = "miniverse-redis"
    REDIS_CHANNEL_NAME: str = "miniverse-updates"
    KEYCLOAK_ISSUER: str = "http://keycloak:8080/keycloak/"
    KEYCLOAK_REALM: str = "miniverse"
    KEYCLOAK_CLIENT_ID: str = "miniverse-client"
    DOMAIN_NAME: str = "miniverse.fr"


settings = Settings()
# Ensure the data path exists
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
