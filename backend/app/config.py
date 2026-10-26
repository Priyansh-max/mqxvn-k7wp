import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_DEFAULT_CACHE = Path(__file__).resolve().parents[2] / "data" / "cache"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    elexon_base_url: str = "https://data.elexon.co.uk/bmrs/api/v1"
    # Optional; Insights API is public. Kept for future-proofing / proxied gateways.
    elexon_api_key: str | None = None
    cache_dir: Path = Path(os.environ.get("CACHE_DIR", str(_DEFAULT_CACHE)))
    cors_origins: str = "*"
    delivery_month: str = "2026-01"


settings = Settings()
settings.cache_dir.mkdir(parents=True, exist_ok=True)
