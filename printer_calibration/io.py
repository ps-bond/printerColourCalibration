
"""CSV loading helpers for measurement files.

This loader is tolerant of comment lines (starting with '#'), extra
columns, and common casing/whitespace differences in column names. It
ensures the returned DataFrame contains the canonical columns
`patch`, `rgb`, `L`, `a`, `b` and that numeric LAB values are coerced
to numbers where possible.
"""

import warnings

import pandas as pd

# canonical required column names (note capital 'L')
CANONICAL_ANALYSIS_COLUMNS = {"patch", "L", "a", "b"}


def _normalize_columns(columns):
    """Return a rename mapping from original column name -> canonical name.

    The function matches columns case-insensitively and strips
    surrounding whitespace. For example ' l ' or 'L' -> 'L'.
    """
    canon = {
        "patch": "patch",
        "label": "patch",  # Map 'label' to 'patch'
        "l": "L",
        "a_lab": "a",      # Map 'a_lab' to 'a'
        "b_lab": "b",      # Map 'b_lab' to 'b'
        "r": "r",          # Keep 'r' as 'r'
        "g": "g",          # Keep 'g' as 'g'
        "b": "b_rgb",      # Map 'b' from r,g,b to 'b_rgb' to avoid conflict with Lab 'b'
    }
    rename = {}
    for col in columns:
        key = col.strip().lower()
        if key in canon:
            rename[col] = canon[key]
    return rename


def load_csv(path):
    """Load a measurement CSV and return a cleaned pandas.DataFrame.

    Parameters
    ----------
    path : str
        Path to the CSV file.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing at least the required columns. Raises
        ``ValueError`` if required columns cannot be found after
        normalization.
    """

    # Try a permissive read that ignores comment lines beginning with '#'.
    try:
        df = pd.read_csv(path, comment="#", skip_blank_lines=True)
    except Exception:
        # Fall back to the python engine which is more permissive with
        # malformed CSV files and mixed delimiters.
        df = pd.read_csv(path, comment="#", skip_blank_lines=True, engine="python")

    # Drop unnamed/index columns often produced by spreadsheets
    unnamed = [c for c in df.columns
               if str(c).lower().startswith("unnamed")]  # pragma: no cover
    if unnamed:
        df = df.drop(columns=unnamed)

    # Normalize column names (strip/case-insensitive) and rename
    rename_map = _normalize_columns(df.columns)
    if rename_map:
        df = df.rename(columns=rename_map)

    # Verify canonical Lab columns are present after normalization
    # 'r', 'g', 'b_rgb' are not strictly required for analysis, but are passed through
    missing_lab_cols = CANONICAL_ANALYSIS_COLUMNS.difference(df.columns)
    if missing_lab_cols:
        raise ValueError(f"CSV must contain core Lab columns {CANONICAL_ANALYSIS_COLUMNS}; missing: {missing_lab_cols}")


    # Coerce numeric Lab values to numbers where possible; be tolerant of
    # non-numeric garbage and drop rows that have no valid Lab data.
    for col in ("L", "a", "b"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Warn and drop rows where all three Lab values are missing
    lab_na = (df[["L", "a", "b"]].isna().all(axis=1))
    if lab_na.any():
        n = lab_na.sum()
        warnings.warn(f"{n} row(s) have no valid L/a/b values and will be dropped")
        df = df.loc[~lab_na].copy()

    # Reset index for a clean DataFrame
    df = df.reset_index(drop=True)

    return df
