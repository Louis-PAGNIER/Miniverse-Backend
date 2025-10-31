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


settings = Settings()
# TODO: check if HOST_DATA_PATH is valid (is not None + does path exist + is dir)
# Ensure the data path exists
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
