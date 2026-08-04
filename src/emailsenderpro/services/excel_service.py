"""Email list loader for CSV and Excel files."""
import logging
from pathlib import Path

import pandas as pd

logger = logging.getLogger(__name__)


def load_emails(file_path: str, column: str | None = None) -> list[str]:
    """Load and clean email addresses from a CSV or Excel file."""
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext == ".csv":
        df = pd.read_csv(file_path)
    elif ext in (".xlsx", ".xls"):
        df = pd.read_excel(file_path)
    else:
        raise ValueError("Unsupported format. Use .csv or .xlsx")

    if column and column in df.columns:
        col_name = column
    else:
        candidates = [c for c in df.columns if c.lower() == "email"]
        if not candidates:
            raise ValueError(f"No 'email' column found. Available: {list(df.columns)}")
        col_name = candidates[0]

    emails = df[col_name].dropna().astype(str).str.strip().tolist()
    emails = [e for e in emails if "@" in e]
    if not emails:
        raise ValueError("No valid email addresses found.")
    logger.info("Loaded %d emails from %s", len(emails), path.name)
    return emails
