#!/usr/bin/env python3
"""
Entry point for: python -m emailsenderpro
"""
import sys
from pathlib import Path

# Auto-fix PYTHONPATH when run as module
if __package__ is None or __package__ == "":
    src_path = Path(__file__).parent.parent.resolve()
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from emailsenderpro.app import main

if __name__ == "__main__":
    main()
