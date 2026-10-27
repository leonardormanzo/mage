from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    app_name: str = "Arc Copilot 1.0"
    environment: str = os.getenv("APP_ENV", "development")
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-change-me")
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'arc_copilot.db').as_posix()}"
    )
    storage_dir: Path = Path(os.getenv("STORAGE_DIR", str(BASE_DIR / "storage")))
    max_upload_mb: int = int(os.getenv("MAX_UPLOAD_MB", "20"))
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    webhook_verify_token: str | None = os.getenv("WHATSAPP_VERIFY_TOKEN")
    webhook_app_secret: str | None = os.getenv("WHATSAPP_APP_SECRET")
    whatsapp_access_token: str | None = os.getenv("WHATSAPP_ACCESS_TOKEN")
    whatsapp_phone_id: str | None = os.getenv("WHATSAPP_PHONE_ID")

    @property
    def ai_mode(self) -> bool:
        return bool(self.gemini_api_key)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.storage_dir.mkdir(parents=True, exist_ok=True)
    return settings
