# ==============================================================================
# Application Configuration
# ==============================================================================
#
# Single source of truth for all environment-driven settings. Uses
# pydantic-settings to validate env vars at startup — the app will fail fast
# with a clear error if a required variable is missing rather than silently
# using None at runtime.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    # ── Database ──────────────────────────────────────────────────────────
    database_url: str = "postgresql://postgres:postgres@db:5432/fastapi_dev"

    # ── AWS Credentials ───────────────────────────────────────────────────
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_region: str = "ap-southeast-1"

    # ── S3 ────────────────────────────────────────────────────────────────
    s3_bucket_name: str = ""

    # ── App Metadata ──────────────────────────────────────────────────────
    app_name: str = "Product Catalog API"
    debug: bool = False
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
