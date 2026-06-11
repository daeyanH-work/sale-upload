"""Processor for My Wireless - (Via Ticket)."""

import pandas as pd
from datetime import datetime

# ── Final 40-column output schema (order matters) ────────────────────────
OUTPUT_COLUMNS = [
    "SalesDate",                                     # 1
    "EmployeeName",                                  # 2
    "LocationName",                                  # 3
    "IsFeature",                                     # 4
    "InvoiceId",                                     # 5
    "LocationId",                                    # 6
    "EmployeeId",                                    # 7
    "ATTUId",                                        # 8
    "DWSMonth",                                      # 9
    "Postpaid_Voice_Activation_Starter",             # 10
    "VGA_CT",                                        # 11
    "CRU_FN_VGA",                                    # 12
    "Innovative_and_New_Product_Count",              # 13
    "Postpaid_Voice_Activation_Premium",             # 14
    "Postpaid_Voice_Activation_Extra",               # 15
    "Postpaid_Voice_Activation_Value",               # 16
    "Postpaid_Voice_Upgrade",                        # 17
    "Fiber_Activation_500MB_or_Greater",             # 18
    "Fiber_or_Broadband_Activation_300MB_and_less",  # 19
    "Fiber_Upgrade",                                 # 20
    "Postpaid_Data_Hotspots_Vehicles",               # 21
    "Postpaid_Data_Watches_Tablets",                 # 22
    "Protect_Advantage_4_CA",                        # 23
    "Protect_Advantage_4_Non_CA",                    # 24
    "Protect_Advantage_1",                           # 25
    "HomeTech_Protection",                           # 26
    "DirecTV_Activation_with_Equipment",             # 27
    "Postpaid_Wireless_Home_Phone_Activation",       # 28
    "Access_Line_and_ConnecTech_Activation",         # 29
    "Prepaid_Voice_Activation",                      # 30
    "Premium_Accessories",                           # 31
    "DFIndicator",                                   # 32
    "WIREDindicator",                                # 33
    "Internet_Air_Activation",                       # 34
    "CRU",                                           # 35
    "FN",                                            # 36
    "IsAIA",                                         # 37
    "IsVGA",                                         # 38
    "GP",                                            # 39
    "Opp Count",                                     # 40
]


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    My Wireless transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 40 output columns exist (add empty if missing).
    3. Reorder to the exact 40-column schema.
    4. Return (df, 'SalesDetail_MMDDYYYY.csv').

    Input is CSV only.
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Add any missing output columns as empty
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    # 3. Select and reorder to exact 40-column schema
    df = df[OUTPUT_COLUMNS]

    # 4. Build filename: SalesDetail_MMDDYYYY.csv
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"SalesDetail_{date_str}.csv"
    return df, output_filename
