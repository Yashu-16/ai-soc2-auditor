"""
Centralized application settings.

All configuration must flow through this module. No other file in the
codebase should call os.getenv() directly — this keeps config auditable
and makes it trivial to see every environment dependency the system has
(which itself is a nice thing to point to in a SOC2-flavored project:
config management hygiene is a Trust Services Criteria talking point).
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Database ---
    database_url: str

    # --- AI Layer ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # --- App ---
    app_env: str = "development"
    app_debug: bool = True

    # --- Storage paths ---
    upload_dir: str = "app/uploaded_logs"
    report_dir: str = "app/generated_reports"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor. FastAPI routes/services should depend on
    this function (via Depends(get_settings) or a direct call) rather
    than instantiating Settings() themselves.
    """
    return Settings()