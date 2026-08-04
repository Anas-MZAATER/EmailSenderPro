#!/usr/bin/env python3
"""Allow running as: python -m emailsenderpro"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.resolve()
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from emailsenderpro.app import main

if __name__ == "__main__":
    main()
