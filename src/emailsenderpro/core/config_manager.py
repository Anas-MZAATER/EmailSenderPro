"""JSON configuration persistence with multi-account support."""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)
CONFIG_DIR = Path.home() / ".email_sender_pro"
CONFIG_FILE = CONFIG_DIR / "config.json"


class ConfigManager:
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.config_dir = self.config_path.parent
        self._ensure_dir()
        self._data = self._load()
        self._migrate_old_format()

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

    def _migrate_old_format(self) -> None:
        """Convert old single-account format to new multi-account format."""
        if "accounts" in self._data:
            return  # Already new format
        old_email = self._data.get("email")
        if old_email:
            old_account = {
                "email": old_email,
                "server": self._data.get("server", "smtp.gmail.com"),
                "port": self._data.get("port", 587),
            }
            self._data["accounts"] = [old_account]
            # Clean old keys
            for key in ["email", "server", "port"]:
                self._data.pop(key, None)
            self.save()
            logger.info("Migrated old config format to multi-account format.")

    def save(self) -> None:
        self._ensure_dir()
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)
        logger.info("Configuration saved.")

    def get_accounts(self) -> List[Dict[str, Any]]:
        return self._data.get("accounts", [])

    def set_accounts(self, accounts: List[Dict[str, Any]]) -> None:
        self._data["accounts"] = accounts

    def add_account(self, account: Dict[str, Any]) -> None:
        accounts = self.get_accounts()
        accounts = [a for a in accounts if a.get("email") != account.get("email")]
        accounts.append(account)
        self.set_accounts(accounts)

    def remove_account(self, email: str) -> None:
        self.set_accounts([a for a in self.get_accounts() if a.get("email") != email])

    def get_account(self, email: str) -> Optional[Dict[str, Any]]:
        for a in self.get_accounts():
            if a.get("email") == email:
                return a
        return None

    def clear(self) -> None:
        self._data = {}
        if self.config_path.exists():
            self.config_path.unlink()
        logger.info("Configuration cleared.")
