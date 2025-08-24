from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    JWT_SECRET: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24
    DOCKER_NETWORK_NAME: str = "miniverse_default"

    DATA_PATH: str = "./data"


    class Config:
        env_file = ".env"

settings = Settings()