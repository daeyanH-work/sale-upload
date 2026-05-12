"""Processor for Smart Con (TS Mobility)."""

import pandas as pd
from datetime import datetime

# ── Final 49-column output schema (order & names are the source of truth) ──
OUTPUT_COLUMNS = [
    "DistrictName",          # 1
    "LocationName",          # 2  (raw: LocationName1)
    "EmployeeName",          # 3  (raw: EmployeeName1)
    "UserName",              # 4
    "InvoiceId",             # 5
    "SalesDate",             # 6
    "MobileNumber",          # 7
    "Ban",                   # 8
    "CustomerName",          # 9  – commas stripped
    "ReceiptId",             # 10
    "SKUCode",               # 11
    "ModelNumber",           # 12 – commas stripped
    "DeviceTypeDescription", # 13
    "PVE2",                  # 14
    "PVN2",                  # 15
    "PVP1",                  # 16
    "ValuePlus",             # 17
    "VoiceGrossAdds",        # 18
    "UPGCount1",             # 19
    "PremUpg",               # 20
    "EliteUpg",              # 21
    "Video",                 # 22
    "Broadband",             # 23
    "InternetLT300",         # 24
    "InternetGT300",         # 25
    "DTVNowCount",           # 26
    "Landline",              # 27
    "HomeSolutions1",        # 28
    "PremiumEntertainment",  # 29
    "EntTotal",              # 30
    "Prepaid2",              # 31
    "Tablets1",              # 32
    "Wearable1",             # 33
    "AccRev",                # 34
    "NonAppleRevenue",       # 35
    "AppleRevenue",          # 36
    "ACCCount",              # 37
    "AccessoryGP",           # 38
    "APODivisor",            # 39
    "ReceiptId1",            # 40
    "Protech1",              # 41
    "Protech4",              # 42
    "ProtectTotal",          # 43
    "Hometech",              # 44
    "WirelessHomePhone2",    # 45
    "MiFi2",                 # 46
    "SPTotals2",             # 47
    "GrossAdds",             # 48
    "OpsTotal",              # 49
]

# Column index positions that carry commas and need cleaning (0-based in output)
_CUSTOMER_NAME_COL = "CustomerName"   # output col 9  (I in Excel)
_MODEL_NUMBER_COL  = "ModelNumber"    # output col 12 (L in Excel)


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Smart Con (TS Mobility) transformations:

    1. Strip whitespace from all column names.
    2. Drop column A (index 0 – the first column of the raw file).
    3. Keep the next 49 columns (B → AX in the original = A → AW after drop),
       discarding anything beyond that.
    4. Rename LocationName1 → LocationName and EmployeeName1 → EmployeeName
       (if present by name); otherwise rename by position using OUTPUT_COLUMNS.
    5. Remove commas from CustomerName and ModelNumber.
    6. Guarantee final schema is exactly the 49 OUTPUT_COLUMNS.
    7. Return (df, 'SalesDetail_MMDDYYYY.csv').
    """
    df = df.copy()

    # 1. Normalise column names
    df.columns = [str(c).strip() for c in df.columns]

    # 2. Drop Column A (first column, whatever its name)
    df = df.iloc[:, 1:]

    # 3. Keep only the first 49 columns (drops everything after AW in original)
    df = df.iloc[:, :49]

    # 4a. Rename the "1"-suffixed column headers that arrive from the raw file
    df.rename(
        columns={
            "LocationName1": "LocationName",
            "EmployeeName1": "EmployeeName",
        },
        inplace=True,
    )

    # 4b. If the DataFrame still has 49 columns but wrong names, align by position
    if len(df.columns) == 49:
        df.columns = OUTPUT_COLUMNS
    else:
        # Fewer columns than expected – fill missing ones as empty
        for col in OUTPUT_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        df = df[OUTPUT_COLUMNS]

    # 5. Strip commas from CustomerName and ModelNumber
    for col in (_CUSTOMER_NAME_COL, _MODEL_NUMBER_COL):
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(",", "", regex=False)

    # 6. Final guard – ensure exact schema
    df = df[OUTPUT_COLUMNS]

    # 7. Build filename: SalesDetail_MMDDYYYY
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d")
        date_str = dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        date_str = selected_date.replace("-", "")

    output_filename = f"SalesDetail_{date_str}.csv"
    return df, output_filename
