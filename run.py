#!/usr/bin/env python3
"""
EmailSenderPro Launcher
Handles PYTHONPATH setup automatically so the app works from anywhere.
"""
import sys
from pathlib import Path

# Add src/ to Python path
project_root = Path(__file__).parent.resolve()
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from emailsenderpro.app import main

if __name__ == "__main__":
    main()
