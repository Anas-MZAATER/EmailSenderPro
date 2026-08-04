#!/usr/bin/env python3
"""Application entry point for EmailSenderPro."""
import logging
import sys
from pathlib import Path

if __package__ is None:
    project_root = Path(__file__).parent.parent.parent.resolve()
    src_path = project_root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from emailsenderpro.utils.logger import setup_logging
from emailsenderpro.core.config_manager import ConfigManager
from emailsenderpro.core.credential_manager import CredentialManager
from emailsenderpro.setup_wizard import SetupWizard
from emailsenderpro.dashboard import Dashboard


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    if not ConfigManager.is_configured():
        logger.info("First run detected. Launching setup wizard...")
        wizard = SetupWizard()
        wizard.mainloop()

        if not ConfigManager.is_configured():
            logger.info("Setup cancelled. Exiting.")
            return

    logger.info("Launching dashboard...")
    app = Dashboard()
    app.mainloop()


if __name__ == "__main__":
    main()
