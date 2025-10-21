from pathlib import Path

from pydantic_settings import BaseSettings


# Some settings have default values
class Settings(BaseSettings):
    HOST_MODE: str = "docker"  # Either "docker" or "host"
    JWT_SECRET: str
    PROXY_SECRET: str
    HOST_DATA_PATH: Path
    DATA_PATH: Path = "/app/data"
    SQLALCHEMY_DATABASE_PATH: Path = "/app/data/database.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DOCKER_NETWORK_NAME: str = "miniverse-net"
    REDIS_NETWORK_NAME: str = "miniverse-redis"
    REDIS_CHANNEL_NAME: str = "miniverse-updates"

    class Config:
        env_file = ".env"


settings = Settings()

# Ensure the data path exists
settings.DATA_PATH.mkdir(parents=True, exist_ok=True)
