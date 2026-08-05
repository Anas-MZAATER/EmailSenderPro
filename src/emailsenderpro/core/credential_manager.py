"""Secure password storage with keyring and .env fallback."""
import logging
import os
from pathlib import Path
from typing import Optional

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
SERVICE_NAME = "EmailSenderPro"
ENV_FILE = Path.home() / ".email_sender_pro" / ".env"


class CredentialManager:
    """Manages secure storage of SMTP credentials."""

    def __init__(self):
        self._use_keyring = KEYRING_AVAILABLE
        if not self._use_keyring:
            logger.warning("Keyring not available. Falling back to .env file.")

    def save_password(self, username: str, password: str) -> bool:
        """Save password securely. Returns True on success."""
        if self._use_keyring:
            try:
                keyring.set_password(SERVICE_NAME, username, password)
                logger.info(f"Password saved to keyring for {username}")
                return True
            except Exception as e:
                logger.warning(f"Keyring failed: {e}. Falling back to .env")
                self._use_keyring = False

        # Fallback to .env file
        return self._save_to_env(username, password)

    def get_password(self, username: str) -> Optional[str]:
        """Retrieve password. Returns None if not found."""
        if self._use_keyring:
            try:
                pwd = keyring.get_password(SERVICE_NAME, username)
                if pwd:
                    return pwd
            except Exception as e:
                logger.warning(f"Keyring read failed: {e}")

        # Fallback to .env
        return self._get_from_env(username)

    def delete_password(self, username: str) -> bool:
        """Delete stored password."""
        success = False
        if self._use_keyring:
            try:
                keyring.delete_password(SERVICE_NAME, username)
                success = True
            except Exception:
                pass

        # Also clear from .env if present
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE)
            if os.getenv("SMTP_USER") == username:
                content = ENV_FILE.read_text(encoding="utf-8")
                lines = []
                for line in content.splitlines():
                    if not line.startswith("SMTP_PASSWORD="):
                        lines.append(line)
                ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
                success = True

        return success

    def _save_to_env(self, username: str, password: str) -> bool:
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            f"SMTP_SERVER=smtp.gmail.com",
            f"SMTP_PORT=587",
            f"SMTP_USER={username}",
            f"SMTP_PASSWORD={password}",
            f"USE_TLS=true",
        ]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        logger.info(f"Password saved to .env file for {username}")
        return True

    def _get_from_env(self, username: str) -> Optional[str]:
        if ENV_FILE.exists():
            load_dotenv(ENV_FILE)
            env_user = os.getenv("SMTP_USER")
            if env_user == username:
                return os.getenv("SMTP_PASSWORD")
        return None
