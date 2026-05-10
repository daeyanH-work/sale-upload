"""Processor for Lets Go Wireless."""

import pandas as pd
from datetime import datetime

# ── Column renames (raw name → output name) ──────────────────────────────
COLUMN_RENAMES = {
    "Dealer Code":           "Dealer Code 1",
    "Invoice ID":            "Invoice I D",
    "BAN":                   "Ban",
    "SKU":                   "S K U ",
    "VGA Premium":           "V G A Premium",
    "VGA Extra":             "V G A Extra",
    "VGA Starter":           "V G A Starter",
    "VGA Value":             "V G A Value",
    "VGA Total":             "V G A Total",
    "DTV Sat":               "D T V Sat",
    "DTV Stream":            "D T V Stream",
    "Fiber 1G+":             "Fiber 1 G+",
    "VOIP":                  "Voip",
    "Accessory Revenue ($)": "Accessory Revenue",
    "Non-Apple Revenue ($)": "Non-Apple Revenue",
    "Apple Revenue ($)":     "Apple Revenue",
    "GP ($)":                "Gp",
    "APO Divisor":           "A P O Divisor",
    "PA1 Qty":               "Protech1",
    "PA4 Qty":               "Protech4",
    "Home Qty":              "Hometech",
    "Opps":                  "Ops Totals",
}

# ── Columns to drop from raw file ────────────────────────────────────────
COLUMNS_TO_DROP = ["Internet Air", "VGA Elite"]

# ── Final 48-column output schema (order matters) ────────────────────────
OUTPUT_COLUMNS = [
    "District",                  # 1
    "Location",                  # 2
    "Employee",                  # 3
    "Attuid",                    # 4
    "Dealer Code 1",             # 5
    "Invoice I D",               # 6
    "Sales Date",                # 7
    "Mobile Number",             # 8
    "Ban",                       # 9
    "Customer Name",             # 10  – commas stripped
    "S K U ",                    # 11
    "Model Number",              # 12  – commas stripped
    "Device Type Description",   # 13  – commas stripped
    "V G A Premium",             # 14
    "V G A Extra",               # 15
    "V G A Starter",             # 16
    "V G A Value",               # 17
    "V G A Total",               # 18
    "Upgrade Count",             # 19
    "Prem Upg",                  # 20
    "Extra Upg",                 # 21
    "D T V Sat",                 # 22
    "D T V Stream",              # 23
    "Broadband",                 # 24
    "Broadband <300",            # 25
    "Fiber 300",                 # 26
    "Fiber 500",                 # 27
    "Fiber 1 G+",                # 28
    "Voip",                      # 29
    "Entertainment Total",       # 30
    "Prepaid",                   # 31
    "Tablets",                   # 32
    "Wearables",                 # 33
    "Accessory Revenue",         # 34
    "Non-Apple Revenue",         # 35
    "Apple Revenue",             # 36
    "Accessory Count",           # 37
    "Gp",                        # 38
    "A P O Divisor",             # 39
    "Receipt Id",                # 40
    "Protech1",                  # 41
    "Protech4",                  # 42
    "Protech Total",             # 43
    "Hometech",                  # 44
    "Wireless Home Phone",       # 45
    "Connected Devices",         # 46
    "Gross Adds",                # 47
    "Ops Totals",                # 48
]

# Columns where commas should be stripped
_COMMA_CLEAN_COLS = ["Customer Name", "Model Number", "Device Type Description"]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Lets Go Wireless transformations:

    1.  Strip whitespace from all column names.
    2.  Remove the last row (totals row).
    3.  Rename columns per COLUMN_RENAMES map.
    4.  Drop Internet Air and VGA Elite columns.
    5.  Replace nulls with 0.
    6.  Strip commas from Customer Name, Model Number, Device Type Description.
    7.  Ensure all 48 output columns exist (add as 0 if missing).
    8.  Reorder to exact 48-column schema.
    9.  Return (df, 'SalesDetail_MMDDYYYY.csv').
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Remove the last row (totals row)
    if len(df) > 0:
        df = df.iloc[:-1]

    # 3. Rename columns
    df.rename(columns=COLUMN_RENAMES, inplace=True)

    # 4. Drop unwanted columns (silently skip if absent)
    df.drop(columns=[c for c in COLUMNS_TO_DROP if c in df.columns], inplace=True)

    # 5. Replace all nulls with 0
    df.fillna(0, inplace=True)

    # 6. Strip commas from specified text columns
    for col in _COMMA_CLEAN_COLS:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False)

    # 7. Ensure every output column exists; add as 0 if missing
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = 0

    # 8. Select and reorder to exact 48-column schema
    df = df[OUTPUT_COLUMNS]

    # 9. Build filename: SalesDetail_MMDDYYYY
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"SalesDetail_{date_str}.csv"
    return df, output_filename
