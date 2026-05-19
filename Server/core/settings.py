from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"


def _parse_csv_or_star(value: str) -> list[str]:
    cleaned = value.strip()
    if not cleaned:
        return []
    if cleaned == "*":
        return ["*"]
    return [item.strip() for item in cleaned.split(",") if item.strip()]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cors_origins: str = Field(default="*", validation_alias="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=False, validation_alias="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: str = Field(default="*", validation_alias="CORS_ALLOW_METHODS")
    cors_allow_headers: str = Field(default="*", validation_alias="CORS_ALLOW_HEADERS")

    @property
    def cors_origin_list(self) -> list[str]:
        return _parse_csv_or_star(self.cors_origins)

    @property
    def cors_method_list(self) -> list[str]:
        return _parse_csv_or_star(self.cors_allow_methods)

    @property
    def cors_header_list(self) -> list[str]:
        return _parse_csv_or_star(self.cors_allow_headers)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

