"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Loaded from .env file."""

    tavily_api_key: str = ""
    seekdb_db_path: str = "./data/seekdb.db"
    llm_api_base: str = ""
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
