"""Processor for AtoZ - (Via Ticket)."""

import pandas as pd
from datetime import datetime

# ── Final 15-column output schema (order matters) ────────────────────────
OUTPUT_COLUMNS = [
    "Store",            # 1
    "Trans ID",         # 2
    "Trans Date Time",  # 3
    "Salesperson",      # 4
    "Customer",         # 5  – commas stripped
    "Email",            # 6
    "Trans Type",       # 7
    "Qty",              # 8
    "GP",               # 9
    "Tax",              # 10
    "Tender Type",      # 11
    "Total Sales",      # 12
    "Category",         # 13
    "Action Type",      # 14
    "Commission Item",  # 15
]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    AtoZ transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 15 output columns exist (add empty if missing).
    3. Reorder to the exact 15-column schema.
    4. Remove commas from the Customer column.
    5. Return (df, 'AtoZ Sales Transaction Details (MTD)- MMDDYYYY.csv').
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 15-column schema
    df = df[OUTPUT_COLUMNS]

    # 4. Strip commas from Customer column
    df["Customer"] = df["Customer"].astype(str).str.replace(",", "", regex=False)

    # 5. Build filename: AtoZ Sales Transaction Details (MTD)- MMDDYYYY.csv
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"AtoZ Sales Transaction Details (MTD)- {date_str}.csv"
    return df, output_filename
