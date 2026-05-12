"""Processor for Global Communications."""

import pandas as pd
from datetime import datetime

# ── Final 49-column output schema (order matters) ─────────────────────
OUTPUT_COLUMNS = [
    "District",                  # 1
    "Location",                  # 2
    "Employee",                  # 3
    "Attuid",                    # 4
    "Dealer Code",               # 5
    "Model Number",              # 6  – commas stripped
    "Invoice ID",                # 7
    "Sales Date",                # 8
    "Mobile Number",             # 9
    "BAN",                       # 10
    "Customer Name",             # 11 – commas stripped
    "SKU",                       # 12
    "Device Type Description",   # 13 – commas stripped
    "VGA Premium",               # 14
    "VGA Extra",                 # 15
    "VGA Starter",               # 16
    "VGA Value",                 # 17
    "VGA Total",                 # 18
    "Upgrade Count",             # 19
    "Prem Upg",                  # 20
    "Extra Upg",                 # 21
    "DTV Sat",                   # 22
    "DTV Stream",                # 23
    "Broadband",                 # 24
    "Broadband <300",            # 25
    "Fiber 300",                 # 26
    "Fiber 500",                 # 27
    "Fiber 1G+",                 # 28
    "VOIP",                      # 29
    "Internet Air",              # 30
    "Entertainment Total",       # 31
    "Prepaid",                   # 32
    "Tablets",                   # 33
    "Wearables",                 # 34
    "Accessory Revenue ($)",     # 35
    "Non-Apple Revenue ($)",     # 36
    "Apple Revenue ($)",         # 37
    "Accessory Count",           # 38
    "GP ($)",                    # 39
    "APO Divisor",               # 40
    "Receipt Id",                # 41
    "PA1 Qty",                   # 42
    "PA4 Qty",                   # 43
    "Protech Total",             # 44
    "Home Qty",                  # 45
    "Wireless Home Phone",       # 46
    "Connected devices",         # 47
    "Gross Adds",                # 48
    "Opps",                      # 49
]

# ── Column rename (raw → output) ──────────────────────────────────────
COLUMN_RENAMES = {
    "Connected Devices": "Connected devices",
}

# ── Columns with commas to strip ──────────────────────────────────────
COMMA_COLUMNS = ["Customer Name", "Model Number", "Device Type Description"]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Apply Global Communications–specific transformations.

    Steps:
      1. Drop the last row (totals row).
      2. Rename columns as needed.
      3. Strip commas from Customer Name, Model Number, Device Type Description.
      4. Reorder / select the 49 output columns.
      5. Return (processed_df, output_filename).
    """
    try:
        df = df.copy()

        # 1. Remove last row (totals)
        df = df.iloc[:-1].reset_index(drop=True)

        # 2. Rename columns
        df = df.rename(columns=COLUMN_RENAMES)

        # 3. Strip commas from specified text columns
        for col in COMMA_COLUMNS:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace(",", "", regex=False)
                    .where(df[col].notna(), other=df[col])
                )

        # 4. Select & reorder to final 49 columns
        missing = [c for c in OUTPUT_COLUMNS if c not in df.columns]
        if missing:
            raise ValueError(
                f"Global Communications: missing expected columns: {missing}"
            )
        df = df[OUTPUT_COLUMNS]

        # 5. Build filename  SalesDetail_MMDDYYYY.csv
        try:
            dt = datetime.strptime(selected_date, "%Y-%m-%d")
            date_str = dt.strftime("%m%d%Y")
        except ValueError:
            date_str = selected_date.replace("-", "")

        filename = f"SalesDetail_{date_str}.csv"
        return df, filename

    except ValueError:
        raise
    except Exception as exc:
        raise RuntimeError(
            f"Global Communications processing failed: {exc}"
        ) from exc
