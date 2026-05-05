"""Processor for USA Cell."""

import pandas as pd
from datetime import datetime

# ── Columns to remove from the uploaded file ────────────────────────────
COLUMNS_TO_DROP = [
    "Related Receipt #",
    "Related Rep ATTUID",
    "Related Rep Username",
    "IMEI1",
    "IMEI2",
]

# ── Final 37-column schema (order matters) ───────────────────────────────
OUTPUT_COLUMNS = [
    "Receipt #",
    "Location Name",
    "Created By ATTUID",
    "Created By Username",
    "Date Created",
    "Customer Name",
    "Client Device",
    "Vendor Name",
    "SKU",
    "Tracking #",
    "Sold as Used",
    "Contract #",
    "Product Name",
    "Refund",
    "Quantity",
    "AR Cost",
    "Total Cost",
    "Catalog Cost",
    "List Price",
    "Selling Price",
    "Original Price",
    "Adjusted Price",
    "Net Profit",
    "Non-Revenue Sales",
    "Net Sales",
    "Pricing Discounts",
    "Total Product Coupons",
    "MDR Amount",
    "Product Category",
    "Product Sub Category",
    "Product Type",
    "Port-In",
    "Direct Fulfillment",
    "BAN",
    "CTN",
    "MS State TAX AMOUNT",
    "MS State EXEMPTION NUMBER - EXEMPTION REASON",
]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    USA Cell transformations:
    1. Strip whitespace from all column names.
    2. Drop the 5 unwanted columns.
    3. Rename the quoted/spaced MS State EXEMPTION column.
    4. Reorder / fill to the exact 37-column output schema.
    5. Return (df, 'Sales_Details_MMDDYYYY.csv').
    """
    df = df.copy()

    # 1. Strip leading/trailing whitespace (and stray quotes) from column names
    df.columns = [c.strip().strip('"') for c in df.columns]

    # 2. Drop unwanted columns (silently skip if already absent)
    df.drop(
        columns=[c for c in COLUMNS_TO_DROP if c in df.columns],
        inplace=True,
    )

    # 3. Normalise any remaining column-name whitespace (e.g. "Net Profit ")
    df.columns = [c.strip() for c in df.columns]

    # 4. Ensure every output column exists; add as empty if missing
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 5. Select and reorder to the exact 37-column schema
    df = df[OUTPUT_COLUMNS]

    # 6. Build output filename: Sales_Details_MMDDYYYY
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"Sales_Details_{date_str}.csv"
    return df, output_filename
