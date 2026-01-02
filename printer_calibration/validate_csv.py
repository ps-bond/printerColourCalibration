"""Small CSV validation utility for printer_calibration measurement files.

Usage:

    python -m printer_calibration.validate_csv path/to/file.csv

The script will exit with status 0 if the CSV is valid, and non-zero if
validation fails.
"""

import argparse
import sys

from .io import load_csv


def validate(path: str) -> None:
    """Load and validate the CSV file. Raises ValueError on failure."""
    # load_csv already checks REQUIRED and raises ValueError if missing
    df = load_csv(path)
    # Additional sanity checks can be added here if needed
    if df.empty:
        raise ValueError("CSV appears to be empty")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m printer_calibration.validate_csv",
        description="Validate measurement CSV file for required columns",
    )
    parser.add_argument("path", help="Path to the measurement CSV file")
    args = parser.parse_args()

    try:
        validate(args.path)
    except Exception as exc:  # pragma: no cover - top-level reporting
        print(f"Validation failed: {exc}", file=sys.stderr)
        sys.exit(2)

    print("CSV validation: OK")


if __name__ == "__main__":
    main()
