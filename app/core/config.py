from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    JWT_SECRET: str
    HOST_DATA_PATH: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DOCKER_NETWORK_NAME: str = "miniverse-net"

    class Config:
        env_file = ".env"

settings = Settings()
DATA_PATH = Path("/app/data")

# Ensure the data path exists
DATA_PATH.mkdir(parents=True, exist_ok=True)