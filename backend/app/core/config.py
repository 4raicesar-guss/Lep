from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    bot_token: str = ""
    database_url: str = "postgresql+asyncpg://granja:granja_dev@localhost:5432/granja"
    redis_url: str = "redis://localhost:6379/0"
    auth_timeout: int = 86400

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
