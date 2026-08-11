"""Processor for Mobile One - (Via Ticket)."""

import pandas as pd
from datetime import datetime, timedelta

# Excel's day-0 origin (accounts for Excel's 1900 leap-year bug) — the same
# origin pandas itself uses for unit="D" Excel-serial conversions.
_EXCEL_EPOCH = datetime(1899, 12, 30)

# ── Final 14-column output schema (order matters) ────────────────────────
OUTPUT_COLUMNS = [
    "Date",                 # 1
    "ActDate",              # 2
    "DeactDate",            # 3
    "ReactDate",            # 4
    "ServiceUniversalID",   # 5  – formatted as text, value unchanged
    "Store",                # 6
    "SAP",                  # 7
    "Employee",              # 8
    "File",                 # 9
    "ProductType",          # 10
    "SOCDescription",       # 11
    "ActivityType",         # 12
    "Boxes",                # 13
    "Net Revenue",          # 14
]


def _to_text(series: pd.Series) -> pd.Series:
    """
    Format a column as plain text without altering its underlying value —
    only undoes accidental numeric parsing (e.g. 123 read as 123.0).
    """
    def conv(v):
        if pd.isna(v):
            return ""
        if isinstance(v, float) and v.is_integer():
            return str(int(v))
        return str(v)
    return series.apply(conv)


def _parse_one_date(v):
    """
    Parse a single cell into a date, handling every shape Excel/pandas
    might hand back: a real datetime/Timestamp, a raw Excel serial number
    (when openpyxl didn't recognize the cell's number format as a date),
    or a date string like "8/1/2026". Returns None if unparseable.
    """
    if pd.isna(v):
        return None
    if isinstance(v, (pd.Timestamp, datetime)):
        return v
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        try:
            return _EXCEL_EPOCH + timedelta(days=float(v))
        except (ValueError, OverflowError, OSError):
            return None
    parsed = pd.to_datetime(v, errors="coerce")
    return None if pd.isna(parsed) else parsed


def _format_date(series: pd.Series) -> pd.Series:
    """
    Keep date columns as M/D/YYYY text (e.g. 8/1/2026) instead of letting
    Excel re-render them as a raw date serial number (e.g. 46235). Blank
    cells stay blank; unparseable non-blank values are left untouched.
    """
    def fmt(v):
        ts = _parse_one_date(v)
        if ts is None:
            return "" if pd.isna(v) or str(v).strip() == "" else v
        return f"{ts.month}/{ts.day}/{ts.year}"

    return series.apply(fmt)


def _format_currency(series: pd.Series) -> pd.Series:
    """
    Keep Net Revenue in the original currency text style — "$196.34 " for
    positive amounts, "($114.00)" for negative — instead of a bare number
    (e.g. 196.34, -114). Excel stores this cell as a plain number with a
    currency display format, so the "$"/parentheses aren't part of the raw
    value pandas reads; this reconstructs that same display without
    altering the underlying amount. Non-numeric values are left untouched.
    """
    def fmt(v):
        if pd.isna(v) or str(v).strip() == "":
            return ""
        try:
            cleaned = str(v).strip().replace("$", "").replace(",", "")
            if cleaned.startswith("(") and cleaned.endswith(")"):
                cleaned = "-" + cleaned[1:-1]
            num = float(cleaned)
        except ValueError:
            return v
        if num < 0:
            return f"(${abs(num):,.2f})"
        return f"${num:,.2f} "

    return series.apply(fmt)


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Mobile One transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 14 output columns exist (add empty if missing).
    3. Reorder to the exact 14-column schema (drops any extra columns).
    4. Drop fully blank rows (e.g. trailing blank rows past the last data row).
    5. Format ServiceUniversalID as text (data value unchanged).
    6. Keep Date, ActDate, DeactDate, ReactDate as M/D/YYYY text
       instead of a raw Excel date serial number.
    7. Keep Net Revenue in currency text form ($X.XX / ($X.XX) for
       negatives) instead of a bare number.
    8. Return (df, 'SalesDetail_MMDDYYYY.xlsx').

    Input and output are both xlsx.
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 14-column schema — drops any extra columns
    df = df[OUTPUT_COLUMNS]

    # 4. Drop rows that are entirely blank (whitespace-only counts as blank)
    df = df.replace(r"^\s*$", pd.NA, regex=True).dropna(how="all").reset_index(drop=True)

    # 5. Format ServiceUniversalID as text (value unchanged)
    df["ServiceUniversalID"] = _to_text(df["ServiceUniversalID"])

    # 6. Keep date columns as M/D/YYYY text
    for col in ("Date", "ActDate", "DeactDate", "ReactDate"):
        df[col] = _format_date(df[col])

    # 7. Keep Net Revenue in currency text form
    df["Net Revenue"] = _format_currency(df["Net Revenue"])

    # 8. Build filename: SalesDetail_MMDDYYYY.xlsx
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"SalesDetail_{date_str}.xlsx"
    return df, output_filename
