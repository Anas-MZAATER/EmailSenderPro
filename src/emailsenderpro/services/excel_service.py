"""CSV / Excel file reader for recipient lists."""
import logging
from pathlib import Path
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def load_emails(file_path: str) -> List[str]:
    """Load email addresses from a CSV or Excel file.

    The file must contain a column named 'email'.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if path.suffix.lower() == ".csv":
        df = pd.read_csv(file_path)
    elif path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

    if "email" not in df.columns:
        raise ValueError("The file must contain a column named 'email'.")

    emails = df["email"].dropna().astype(str).str.strip().tolist()
    emails = [e for e in emails if "@" in e]

    logger.info(f"Loaded {len(emails)} emails from {file_path}")
    return emails
