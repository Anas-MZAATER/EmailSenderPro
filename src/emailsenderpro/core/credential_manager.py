"""Secure credential storage with Windows Credential Manager fallback."""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

SERVICE_NAME = "EmailSenderPro"
ENV_FILE = Path.home() / ".email_sender_pro" / ".env"

try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

try:
    from dotenv import load_dotenv, set_key
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False


class CredentialManager:
    """Store/retrieve the Gmail App Password securely."""

    @classmethod
    def _ensure_dir(cls) -> None:
        ENV_FILE.parent.mkdir(parents=True, exist_ok=True)

    @classmethod
    def save_password(cls, password: str) -> None:
        if KEYRING_AVAILABLE:
            try:
                keyring.set_password(SERVICE_NAME, "gmail_password", password)
                logger.info("Password stored in system keyring.")
                return
            except Exception as exc:
                logger.warning("Keyring failed (%s), falling back to .env", exc)

        if DOTENV_AVAILABLE:
            cls._ensure_dir()
            set_key(str(ENV_FILE), "SMTP_PASSWORD", password)
            logger.info("Password stored in .env fallback.")
        else:
            raise RuntimeError(
                "No secure storage available. Install 'keyring' or 'python-dotenv'."
            )

    @classmethod
    def get_password(cls) -> str | None:
        if KEYRING_AVAILABLE:
            try:
                pwd = keyring.get_password(SERVICE_NAME, "gmail_password")
                if pwd:
                    return pwd
            except Exception as exc:
                logger.warning("Keyring retrieval failed: %s", exc)

        if DOTENV_AVAILABLE and ENV_FILE.exists():
            load_dotenv(ENV_FILE)
            pwd = os.getenv("SMTP_PASSWORD")
            if pwd:
                return pwd
        return None

    @classmethod
    def delete_password(cls) -> None:
        if KEYRING_AVAILABLE:
            try:
                keyring.delete_password(SERVICE_NAME, "gmail_password")
            except Exception:
                pass
        if ENV_FILE.exists():
            lines = [line for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
                     if not line.startswith("SMTP_PASSWORD=")]
            ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
            logger.info("Password removed from .env fallback.")
