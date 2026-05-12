"""Processor for Marnics."""

import pandas as pd
from datetime import datetime

# ── Final 25-column output schema (order matters) ────────────────────────
OUTPUT_COLUMNS = [
    "Store Name",         # 1
    "Date",               # 2
    "Invoice ID",         # 3
    "Customer",           # 4
    "Email Address",      # 5
    "Phone Number",       # 6
    "Customer Group",     # 7
    "Type",               # 8
    "Ticket ID",          # 9
    "Created By",         # 10
    "Assigned To",        # 11
    "Category",           # 12
    "Product Name",       # 13
    "Serial",             # 14
    "Color",              # 15
    "Size",               # 16
    "Network",            # 17
    "Condition",          # 18
    "Quantity",           # 19
    "Total Sales",        # 20
    "Discount",           # 21
    "COGS",               # 22
    "Net Profit",         # 23
    "Net Profit Margin",  # 24
    "Tax",                # 25
]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Marnics transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 25 output columns exist (add empty if missing).
    3. Reorder to the exact 25-column schema.
    4. Return (df, 'Item Wise Sales Report MM-DD-YYYY.xlsx').

    Input and output are both xlsx.
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 25-column schema
    df = df[OUTPUT_COLUMNS]

    # 4. Build filename: Item Wise Sales Report MM-DD-YYYY.xlsx
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m-%d-%Y")
    except (ValueError, TypeError):
        date_str = selected_date

    output_filename = f"Item Wise Sales Report {date_str}.xlsx"
    return df, output_filename
