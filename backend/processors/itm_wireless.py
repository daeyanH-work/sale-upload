"""Processor for ITM Wireless."""

import pandas as pd
from datetime import datetime

# ── Final 16-column output schema (order matters) ────────────────────────
OUTPUT_COLUMNS = [
    "Store",            # 1
    "Trans ID",         # 2
    "Trans Date Time",  # 3
    "Salesperson",      # 4
    "Customer",         # 5
    "Email",            # 6
    "Trans Type",       # 7
    "Product Desc",     # 8
    "Qty",              # 9
    "GP",               # 10
    "Tax",              # 11
    "Tender Type",      # 12
    "Total Sales",      # 13
    "Category",         # 14
    "Action Type",      # 15
    "Commission Item",  # 16
]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    ITM Wireless transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 16 output columns exist (add empty if missing).
    3. Reorder to the exact 16-column schema (drops any extra columns).
    4. Return (df, 'ITM_Wireless_MTD_Sales_-_Rebiz_MMDDYYYY-MMDDYYYY.xlsx').

    Input is csv (comma-delimited); output is xlsx.
    The filename spans month-to-date: 1st of the selected month → selected date.
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 16-column schema — drops any extra columns
    df = df[OUTPUT_COLUMNS]

    # 4. Build filename: ITM_Wireless_MTD_Sales_-_Rebiz_<1st of month>-<selected date>.xlsx
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        start_str = dt.replace(day=1).strftime("%m%d%Y")
        end_str = dt.strftime("%m%d%Y")
        date_range = f"{start_str}-{end_str}"
    except (ValueError, TypeError):
        date_range = selected_date.replace("-", "")

    output_filename = f"ITM_Wireless_MTD_Sales_-_Rebiz_{date_range}.xlsx"
    return df, output_filename
