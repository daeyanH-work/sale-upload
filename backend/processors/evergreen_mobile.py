"""Processor for Evergreen Mobile - (Via Ticket)."""

import pandas as pd
from datetime import datetime

# ── Final 12-column output schema (order matters) ───────────────────────
OUTPUT_COLUMNS = [
    "Store",            # 1
    "Trans Date Time",  # 2
    "Trans ID",         # 3
    "Salesperson",      # 4
    "Customer",         # 5  – commas stripped
    "Email",            # 6
    "Trans Type",       # 7
    "Qty",              # 8
    "GP",               # 9
    "Category",         # 10
    "Action Type",      # 11
    "Commission Item",  # 12
]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Evergreen Mobile transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 12 output columns exist (add empty if missing).
    3. Reorder to the exact 12-column schema.
    4. Remove commas from the Customer column.
    5. Return (df, 'MTD Sales Transaction Details (Rebiz) - MM-DD-YYYY.csv').
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 12-column schema
    df = df[OUTPUT_COLUMNS]

    # 4. Strip commas from Customer column
    df["Customer"] = df["Customer"].astype(str).str.replace(",", "", regex=False)

    # 5. Build filename: MTD Sales Transaction Details (Rebiz) - MM-DD-YYYY.csv
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m-%d-%Y")
    except (ValueError, TypeError):
        date_str = selected_date

    output_filename = f"MTD Sales Transaction Details (Rebiz) - {date_str}.csv"
    return df, output_filename
