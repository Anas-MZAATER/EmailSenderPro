#!/usr/bin/env python3
"""
EmailSenderPro - Cross-platform launcher
Adds src/ to PYTHONPATH before importing the package.
"""
import sys
from pathlib import Path

# Add src/ to PYTHONPATH so 'emailsenderpro' can be imported
PROJECT_ROOT = Path(__file__).parent.resolve()
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from emailsenderpro.app import main

if __name__ == "__main__":
    main()
