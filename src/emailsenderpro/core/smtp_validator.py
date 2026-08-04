"""SMTP validation service."""
import logging
import smtplib

logger = logging.getLogger(__name__)


class SMTPValidationError(Exception):
    """Raised when SMTP authentication fails."""


def validate_smtp(email: str, password: str, server: str = "smtp.gmail.com", port: int = 587) -> bool:
    """Test login against the SMTP server using STARTTLS."""
    try:
        with smtplib.SMTP(server, port, timeout=10) as srv:
            srv.starttls()
            srv.login(email, password)
        logger.info("SMTP validation successful for %s", email)
        return True
    except smtplib.SMTPAuthenticationError as exc:
        raise SMTPValidationError("Authentication failed. Use a Gmail App Password, not your regular password.") from exc
    except Exception as exc:
        raise SMTPValidationError(f"Connection error: {exc}") from exc
