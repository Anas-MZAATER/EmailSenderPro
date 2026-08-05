"""Application bootstrap — decides between setup wizard and dashboard."""
import logging

from emailsenderpro.utils.logger import setup_logger
from emailsenderpro.dashboard import Dashboard

logger = setup_logger()


def main():
    """Launch the application."""
    logger.info("Launching EmailSenderPro...")
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
