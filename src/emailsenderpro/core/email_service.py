"""Core email delivery logic."""
import json
import logging
import random
import smtplib
import threading
import time
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from pathlib import Path
from typing import Callable, List, Optional

logger = logging.getLogger(__name__)

SENT_FILE = Path("sent.json")


class EmailService:
    """Handles bulk email sending with rotation, delays, and resume support."""

    def __init__(
        self,
        accounts: List[str],
        subject: str,
        body: str,
        is_html: bool = False,
        attachments: Optional[List[str]] = None,
        min_delay: int = 60,
        max_delay: int = 300,
        dry_run: bool = False,
        resume: bool = True,
        shuffle: bool = False,
        stop_event: Optional[threading.Event] = None,
    ):
        self.accounts = self._parse_accounts(accounts)
        self.subject = subject
        self.body = body
        self.is_html = is_html
        self.attachments = attachments or []
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.dry_run = dry_run
        self.resume = resume
        self.shuffle = shuffle
        self.sent_emails = self._load_sent()
        self.log_callback: Optional[Callable[[str], None]] = None
        self.progress_callback: Optional[Callable[[int, int], None]] = None
        self.stop_event = stop_event or threading.Event()

    def _parse_accounts(self, accounts: List[str]) -> List[dict]:
        parsed = []
        for acc in accounts:
            parts = acc.strip().split(":")
            if len(parts) >= 4:
                parsed.append({
                    "email": parts[0].strip(),
                    "password": parts[1].strip(),
                    "server": parts[2].strip(),
                    "port": int(parts[3].strip()),
                })
        return parsed

    def _load_sent(self) -> set:
        if not self.resume or not SENT_FILE.exists():
            return set()
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data.get("sent", []))
        except Exception:
            return set()

    def _save_sent(self, email: str) -> None:
        self.sent_emails.add(email)
        try:
            with open(SENT_FILE, "w", encoding="utf-8") as f:
                json.dump({"sent": list(self.sent_emails)}, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save sent log: {e}")

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        self.log_callback = callback

    def set_progress_callback(self, callback: Callable[[int, int], None]) -> None:
        """Callback(current_index, total_count) called after each email."""
        self.progress_callback = callback

    def _log(self, message: str, level: str = "info") -> None:
        logger.log(getattr(logging, level.upper(), logging.INFO), message)
        if self.log_callback:
            self.log_callback(message)

    def _report_progress(self, current: int, total: int) -> None:
        if self.progress_callback:
            self.progress_callback(current, total)

    def send_bulk(self, recipients: List[str]) -> dict:
        """Send emails to all recipients. Returns stats dict."""
        if self.shuffle:
            random.shuffle(recipients)

        stats = {"total": len(recipients), "sent": 0, "skipped": 0, "failed": 0, "stopped": False}
        account_idx = 0
        total = len(recipients)

        for i, recipient in enumerate(recipients):
            if self.stop_event.is_set():
                self._log("Stop requested. Aborting...")
                stats["stopped"] = True
                break

            if self.resume and recipient in self.sent_emails:
                self._log(f"Skipping {recipient} (already sent)")
                stats["skipped"] += 1
                self._report_progress(i + 1, total)
                continue

            account = self.accounts[account_idx % len(self.accounts)]
            account_idx += 1

            success = self._send_single(recipient, account)
            if success:
                stats["sent"] += 1
                self._save_sent(recipient)
            else:
                stats["failed"] += 1

            self._report_progress(i + 1, total)

            if i < len(recipients) - 1 and not self.stop_event.is_set():
                delay = random.randint(self.min_delay, self.max_delay)
                self._log(f"Waiting {delay}s before next send...")
                self._interruptible_sleep(delay)

        self._log(
            f"Done! Sent: {stats['sent']}, Skipped: {stats['skipped']}, "
            f"Failed: {stats['failed']}, Stopped: {stats['stopped']}"
        )
        return stats

    def _interruptible_sleep(self, seconds: int) -> None:
        """Sleep that can be interrupted by stop_event."""
        for _ in range(seconds):
            if self.stop_event.is_set():
                break
            time.sleep(1)

    def _send_single(self, recipient: str, account: dict) -> bool:
        if self.stop_event.is_set():
            return False

        if self.dry_run:
            self._log(f"[DRY-RUN] Would send to {recipient} via {account['email']}")
            return True

        try:
            msg = MIMEMultipart()
            msg["From"] = account["email"]
            msg["To"] = recipient
            msg["Subject"] = self.subject

            content_type = "html" if self.is_html else "plain"
            msg.attach(MIMEText(self.body, content_type, "utf-8"))

            for att_path in self.attachments:
                path = Path(att_path)
                if path.exists():
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(path.read_bytes())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename= {path.name}",
                    )
                    msg.attach(part)

            with smtplib.SMTP(account["server"], account["port"], timeout=30) as server:
                server.ehlo()
                server.starttls()
                server.ehlo()
                server.login(account["email"], account["password"])
                server.sendmail(account["email"], recipient, msg.as_string())

            self._log(f"Sent to {recipient} via {account['email']}")
            return True

        except Exception as e:
            self._log(f"Failed to send to {recipient}: {str(e)}", "error")
            return False
