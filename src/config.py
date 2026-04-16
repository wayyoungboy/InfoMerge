"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loaded from .env file."""

    tavily_api_key: str = ""
    seekdb_db_path: str = "./data/seekdb.db"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
