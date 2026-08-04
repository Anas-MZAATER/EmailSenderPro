"""Application configuration manager (non-sensitive data)."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".email_sender_pro"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "email": "",
    "remember": True,
    "delay_min": 60,
    "delay_max": 300,
    "version": 1,
}


class ConfigManager:
    """Handle persistence of user preferences."""

    @classmethod
    def _ensure_dir(cls) -> None:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls) -> dict:
        if not CONFIG_FILE.exists():
            return DEFAULT_CONFIG.copy()
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, value in DEFAULT_CONFIG.items():
                data.setdefault(key, value)
            return data
        except Exception as exc:
            logger.error("Failed to load config: %s", exc)
            return DEFAULT_CONFIG.copy()

    @classmethod
    def save(cls, data: dict) -> None:
        cls._ensure_dir()
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            logger.info("Configuration saved.")
        except Exception as exc:
            logger.error("Failed to save config: %s", exc)
            raise

    @classmethod
    def get_email(cls) -> str:
        return cls.load().get("email", "")

    @classmethod
    def set_email(cls, email: str) -> None:
        data = cls.load()
        data["email"] = email
        cls.save(data)

    @classmethod
    def is_configured(cls) -> bool:
        return bool(cls.get_email())
