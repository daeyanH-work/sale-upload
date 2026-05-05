"""Processor for USA Cell."""

import pandas as pd
from datetime import datetime

# ── Columns to drop from the raw uploaded file ──────────────────────────
COLUMNS_TO_DROP = [
    "Related Receipt #",
    "Related Rep ATTUID",
    "Related Rep Username",
    "IMEI1",
    "IMEI2",
    "MDR Amount",
]

# ── Final 37-column output schema (order matters) ────────────────────────
# MDR Amount removed; MS State EXEMPTION NUMBER - EXEMPTION REASON split into 2
OUTPUT_COLUMNS = [
    "Receipt #",              # 1
    "Location Name",          # 2
    "Created By ATTUID",      # 3
    "Created By Username",    # 4
    "Date Created",           # 5
    "Customer Name",          # 6
    "Client Device",          # 7
    "Vendor Name",            # 8
    "SKU",                    # 9
    "Tracking #",             # 10
    "Sold as Used",           # 11
    "Contract #",             # 12
    "Product Name",           # 13
    "Refund",                 # 14
    "Quantity",               # 15
    "AR Cost",                # 16
    "Total Cost",             # 17
    "Catalog Cost",           # 18
    "List Price",             # 19
    "Selling Price",          # 20
    "Original Price",         # 21
    "Adjusted Price",         # 22
    "Net Profit",             # 23
    "Non-Revenue Sales",      # 24
    "Net Sales",              # 25
    "Pricing Discounts",      # 26
    "Total Product Coupons",  # 27
    "Product Category",       # 28
    "Product Sub Category",   # 29
    "Product Type",           # 30
    "Port-In",                # 31
    "Direct Fulfillment",     # 32
    "BAN",                    # 33
    "CTN",                    # 34
    "MS State TAX AMOUNT",    # 35
    "MS State EXEMPTION NUMBER",        # 36
    "MS State EXEMPTION REASON",        # 37
]

# Source column that gets split into the two EXEMPTION columns
_EXEMPTION_SOURCE = "MS State EXEMPTION NUMBER - EXEMPTION REASON"


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    USA Cell transformations:
    1.  Strip whitespace / stray quotes from every column name.
    2.  Drop 6 unwanted columns (Related Receipt #, Related Rep ATTUID,
        Related Rep Username, IMEI1, IMEI2, MDR Amount).
    3.  Split `MS State EXEMPTION NUMBER - EXEMPTION REASON` into
        `MS State EXEMPTION NUMBER` and `MS State EXEMPTION REASON`.
    4.  Ensure all 37 output columns exist (add empty if missing).
    5.  Reorder to the exact 37-column schema.
    6.  Return (df, 'Sales_Details_MMDDYYYY.csv').
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [c.strip().strip('"') for c in df.columns]

    # 2. Drop unwanted columns (silently skip any already absent)
    df.drop(
        columns=[c for c in COLUMNS_TO_DROP if c in df.columns],
        inplace=True,
    )

    # 3. Split the combined EXEMPTION column into two separate columns
    if _EXEMPTION_SOURCE in df.columns:
        split_data = (
            df[_EXEMPTION_SOURCE]
            .astype(str)
            .str.strip()
            .str.split(r"\s*-\s*", n=1, expand=True)
        )
        df["MS State EXEMPTION NUMBER"] = split_data[0].replace("nan", "")
        df["MS State EXEMPTION REASON"] = (
            split_data[1].replace("nan", "") if 1 in split_data.columns else ""
        )
        df.drop(columns=[_EXEMPTION_SOURCE], inplace=True)
    else:
        # Source column missing – create both as empty
        df["MS State EXEMPTION NUMBER"] = ""
        df["MS State EXEMPTION REASON"] = ""

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
