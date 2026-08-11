"""Processor for MAA Wireless - (Via Ticket)."""

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
    "GP",               # 10 – converted to numeric
    "Tender Type",      # 11
    "Total Sales",      # 12
    "Category",         # 13
    "Action Type",      # 14
    "Commission Item",  # 15
    "Tax",              # 16
]


def _format_trans_date_time(series: pd.Series) -> pd.Series:
    """
    Keep 'Trans Date Time' in M/D/YYYY H:MM:SS AM/PM (e.g. 8/6/2026 11:50:58 PM)
    instead of letting Excel re-render it as a datetime cell (e.g. 2026-08-06 23:50:58).
    Values that can't be parsed as a date are left untouched.
    """
    parsed = pd.to_datetime(series, errors="coerce")

    def fmt(original, ts):
        if pd.isna(ts):
            return original
        hour12 = ts.hour % 12 or 12
        ampm = "AM" if ts.hour < 12 else "PM"
        return f"{ts.month}/{ts.day}/{ts.year} {hour12}:{ts.minute:02d}:{ts.second:02d} {ampm}"

    return pd.Series(
        [fmt(o, t) for o, t in zip(series, parsed)],
        index=series.index,
    )


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    MAA Wireless transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 16 output columns exist (add empty if missing).
    3. Reorder to the exact 16-column schema.
    4. Convert the GP column to numeric.
    5. Replace blank Tax values with 0.
    6. Format Trans Date Time as M/D/YYYY H:MM:SS AM/PM (not re-formatted by Excel).
    7. Return (df, 'MAA_Sales_Transaction_Details_-_Rebiz_MMDDYYYY.xlsx').

    Input and output are both xlsx.
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 16-column schema
    df = df[OUTPUT_COLUMNS]

    # 4. Convert GP column to numeric
    df["GP"] = pd.to_numeric(df["GP"], errors="coerce").fillna(0)

    # 5. Replace blank Tax values with 0
    df["Tax"] = df["Tax"].apply(lambda v: 0 if pd.isna(v) or str(v).strip() == "" else v)

    # 6. Keep Trans Date Time in M/D/YYYY H:MM:SS AM/PM
    df["Trans Date Time"] = _format_trans_date_time(df["Trans Date Time"])

    # 7. Build filename: MAA_Sales_Transaction_Details_-_Rebiz_MMDDYYYY.xlsx
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"MAA_Sales_Transaction_Details_-_Rebiz_{date_str}.xlsx"
    return df, output_filename
