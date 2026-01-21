from pathlib import Path

from pydantic_settings import BaseSettings


# Some settings have default values
class Settings(BaseSettings):
    PROXY_SOCKS: str | None = None
    JWT_SECRET: str
    PROXY_SECRET: str
    HOST_DATA_PATH: Path
    DATA_PATH: Path = "/app/data"
    SQLALCHEMY_DATABASE_PATH: Path = "/app/data/database.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DOCKER_NETWORK_NAME: str = "miniverse-net"
    REDIS_HOST_NAME: str = "miniverse-redis"
    REDIS_CHANNEL_NAME: str = "miniverse-updates"
    KEYCLOAK_ISSUER: str = "http://keycloak:8080/"
    KEYCLOAK_REALM: str = "miniverse"
    KEYCLOAK_CLIENT_ID: str = "miniverse-client"


settings = Settings()
# Ensure the data path exists
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
