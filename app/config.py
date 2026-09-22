from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Vainu Growth Agent"
    vainu_base_url: str = "https://api.vainu.io/api/v3"
    vainu_token_url: str = "https://api.vainu.io/api/token_authentication/refresh/"
    vainu_refresh_token: str | None = None
    use_mock_vainu: bool = True

    scorer_mode: str = "rules"  # rules | bedrock
    aws_region: str = "eu-north-1"
    bedrock_model_id: str = "eu.anthropic.claude-sonnet-4-20250514-v1:0"

    request_timeout_seconds: float = 20.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
