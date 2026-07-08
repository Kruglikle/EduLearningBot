from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_chat_id: int | None
    admin_ids: set[int]
    project_site: str
    contact_email: str
    contact_telegram: str
    database_url: str
    courses_path: Path
    web_host: str
    web_port: int
    web_allowed_origins: set[str]

    @property
    def sqlite_path(self) -> Path:
        prefix = "sqlite:///"
        if not self.database_url.startswith(prefix):
            raise ValueError("Only sqlite:/// DATABASE_URL is supported in this version")
        raw_path = self.database_url.removeprefix(prefix)
        path = Path(raw_path)
        return path if path.is_absolute() else BASE_DIR / path

    def is_admin(self, user_id: int | None, chat_id: int | None = None) -> bool:
        if user_id is not None and user_id in self.admin_ids:
            return True
        return self.admin_chat_id is not None and chat_id == self.admin_chat_id


def _parse_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Expected integer value, got {value!r}") from exc


def _parse_admin_ids(value: str | None) -> set[int]:
    if not value:
        return set()
    return {int(item.strip()) for item in value.split(",") if item.strip()}


def _parse_origins(value: str | None) -> set[str]:
    if not value:
        return set()
    return {item.strip().rstrip("/") for item in value.split(",") if item.strip()}


def load_settings() -> Settings:
    load_dotenv(BASE_DIR / ".env")
    return Settings(
        bot_token=os.getenv("BOT_TOKEN", ""),
        admin_chat_id=_parse_int(os.getenv("ADMIN_CHAT_ID")),
        admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS")),
        project_site=os.getenv("PROJECT_SITE", "https://edu-learning.ru/"),
        contact_email=os.getenv("CONTACT_EMAIL", ""),
        contact_telegram=os.getenv("CONTACT_TELEGRAM", ""),
        database_url=os.getenv("DATABASE_URL", "sqlite:///edulearning_bot.db"),
        courses_path=BASE_DIR / "bot" / "data" / "courses.json",
        web_host=os.getenv("WEB_HOST", "0.0.0.0"),
        web_port=int(os.getenv("WEB_PORT", "8080")),
        web_allowed_origins=_parse_origins(os.getenv("WEB_ALLOWED_ORIGINS")),
    )
