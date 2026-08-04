"""Core email delivery service with multi-account rotation."""
import logging
import random
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailService:
    """Send emails via SMTP with account rotation and attachment support."""

    def __init__(self, accounts: list[dict], rotation_mode: str = "round_robin"):
        self.accounts = accounts
        self.rotation_mode = rotation_mode
        self._index = 0

    def _next_account(self) -> dict:
        if self.rotation_mode == "random":
            return random.choice(self.accounts)
        acc = self.accounts[self._index % len(self.accounts)]
        self._index += 1
        return acc

    def send(
        self,
        to_addr: str,
        subject: str,
        body: str,
        html: bool = False,
        attachments: list[str] | None = None,
        dry_run: bool = False,
    ) -> bool:
        if dry_run:
            logger.info("[DRY-RUN] Would send to %s", to_addr)
            return True

        account = self._next_account()
        try:
            msg = MIMEMultipart()
            msg["From"] = account["user"]
            msg["To"] = to_addr
            msg["Subject"] = subject

            content_type = "html" if html else "plain"
            msg.attach(MIMEText(body, content_type, "utf-8"))

            if attachments:
                for fp in attachments:
                    try:
                        with open(fp, "rb") as f:
                            part = MIMEBase("application", "octet-stream")
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header(
                                "Content-Disposition",
                                f'attachment; filename="{Path(fp).name}"',
                            )
                            msg.attach(part)
                    except Exception as exc:
                        logger.warning("Attachment error for %s: %s", fp, exc)

            with smtplib.SMTP(account["server"], account["port"], timeout=15) as srv:
                srv.starttls()
                srv.login(account["user"], account["password"])
                srv.sendmail(account["user"], to_addr, msg.as_string())

            logger.info("Sent to %s via %s", to_addr, account["user"])
            return True
        except Exception as exc:
            logger.error("Failed to send to %s: %s", to_addr, exc)
            return False
