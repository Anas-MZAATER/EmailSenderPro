"""JSON configuration persistence."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

CONFIG_DIR = Path.home() / ".email_sender_pro"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigManager:
    """Manages application configuration stored in JSON."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config_dir = self.config_path.parent
        self._ensure_dir()
        self._data = self._load()

    def _ensure_dir(self) -> None:
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def _load(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            return {}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load config: {e}")
            return {}

    def save(self) -> None:
        """Persist current configuration to disk."""
        self._ensure_dir()
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        logger.info("Configuration saved.")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def has_config(self) -> bool:
        return bool(self._data)

    def clear(self) -> None:
        self._data = {}
        if self.config_path.exists():
            self.config_path.unlink()
        logger.info("Configuration cleared.")
