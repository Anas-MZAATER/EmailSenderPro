"""SMTP connection validation."""
import logging
import smtplib
from typing import Tuple

logger = logging.getLogger(__name__)


def validate_smtp(
    email: str,
    password: str,
    server: str = "smtp.gmail.com",
    port: int = 587,
) -> Tuple[bool, str]:
    """Test SMTP credentials by connecting and authenticating.

    Returns:
        (success: bool, message: str)
    """
    try:
        logger.info(f"Testing SMTP connection to {server}:{port}...")
        with smtplib.SMTP(server, port, timeout=10) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(email, password)
            logger.info("SMTP validation successful.")
            return True, "SMTP connection successful!"
    except smtplib.SMTPAuthenticationError:
        logger.error("SMTP authentication failed.")
        return False, "Authentication failed. Use an App Password, not your regular password."
    except smtplib.SMTPConnectError:
        logger.error("Failed to connect to SMTP server.")
        return False, "Could not connect to SMTP server. Check server and port."
    except Exception as e:
        logger.error(f"SMTP validation error: {e}")
        return False, f"Error: {str(e)}"
