"""Processor for Spiked Holding (4-file workflow).

Spiked Holding uploads up to 4 independent files in one go, each
processed and renamed independently:

1. Sale file              (csv -> csv)   process_sale
2. Employee file          (csv -> csv)   process_employee
3. Attendance file        (xlsx -> xlsx) process_attendance
4. Activation Detail file (csv -> csv)   process_activation
"""

import re
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

from .base import _read_file

CSV_MEDIA_TYPE = "text/csv"
XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

# ── Sale file: final 48-column output schema (order matters) ────────────
SALE_OUTPUT_COLUMNS = [
    "marketid", "custno", "company", "item", "itmdesc", "serial", "qty",
    "price", "minprice", "cost", "discount", "realprice", "taxable",
    "taxamount", "pptax", "subtotal", "profit", "adduser", "name",
    "lastname", "invno", "adddate", "custno1", "acttype", "arstat",
    "paytype", "prodline", "category", "subcategory", "paymentsku",
    "cashpaid", "creditcardpaid", "debitcardpaid", "financedpaid",
    "checkpaid", "otherpaid", "artraniid", "armastiid", "firstname",
    "lastname1", "tangible", "serialized", "stationid", "manufacturer",
    "color", "state", "region", "principle",
]

# ── Activation Detail Report: final 32-column output schema ─────────────
ACTIVATION_OUTPUT_COLUMNS = [
    "marketid", "storeid", "company", "custid", "invno", "serial", "item",
    "mobile", "actdate", "account", "ported", "portptn", "reference",
    "sim", "reference1", "custname", "promoname", "linetype", "status",
    "source", "plantype", "accounttype", "term", "prodline", "itmdesc",
    "username", "acttype", "plancode", "plantype1", "grouptype",
    "plandesc", "mrc",
]


def _date_str(selected_date: str, offset_days: int = 0) -> str:
    """Return selected_date (+ offset_days) formatted as MMDDYYYY."""
    try:
        dt = datetime.strptime(selected_date, "%Y-%m-%d") + timedelta(days=offset_days)
        return dt.strftime("%m%d%Y")
    except (ValueError, TypeError):
        return selected_date.replace("-", "")


def _zero_if_not_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0)


def _zero_if_alpha(series: pd.Series) -> pd.Series:
    def fix(val):
        if re.search(r"[A-Za-z]", str(val)):
            return 0
        return val
    return series.apply(fix)


def _to_date_string(series: pd.Series) -> pd.Series:
    """Parse to dates; invalid values become an empty string."""
    return pd.to_datetime(series, errors="coerce").dt.strftime("%m/%d/%Y").fillna("")


def _to_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    df.to_csv(buf, index=False)
    return buf.getvalue()


def process_sale(contents: bytes, filename: str, selected_date: str) -> tuple:
    """
    Sale file transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 48 output columns exist (add empty if missing).
    3. Reorder to the exact 48-column schema.
    4. Remove commas from `itmdesc`.
    5. Replace non-numeric `taxamount` values with 0.
    6. Replace non-numeric `invno` values with 0.
    7. Ensure `adddate` is a valid date (invalid -> blank).
    8. Replace `cashpaid` values containing letters with 0.
    9. Return (csv_bytes, 'SalesDetailReport_MMDDYYYY.csv', media_type, before, after).
    """
    df = _read_file(contents, filename)
    before_count = len(df.columns)
    df = df.copy()

    df.columns = [str(c).strip() for c in df.columns]

    for col in SALE_OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[SALE_OUTPUT_COLUMNS]

    df["itmdesc"] = df["itmdesc"].astype(str).str.replace(",", "", regex=False)
    df["taxamount"] = _zero_if_not_numeric(df["taxamount"])
    df["invno"] = _zero_if_not_numeric(df["invno"])
    df["adddate"] = _to_date_string(df["adddate"])
    df["cashpaid"] = _zero_if_alpha(df["cashpaid"])

    after_count = len(df.columns)
    output_filename = f"SalesDetailReport_{_date_str(selected_date)}.csv"
    return _to_csv_bytes(df), output_filename, CSV_MEDIA_TYPE, before_count, after_count


def process_employee(contents: bytes, filename: str, selected_date: str) -> tuple:
    """
    Employee file: rename only, content unchanged.
    Return (raw_bytes, 'Employee_MMDDYYYY.CSV', media_type, before, after).
    """
    try:
        column_count = len(_read_file(contents, filename).columns)
    except Exception:
        column_count = None

    output_filename = f"Employee_{_date_str(selected_date)}.CSV"
    return contents, output_filename, CSV_MEDIA_TYPE, column_count, column_count


def process_attendance(contents: bytes, filename: str, selected_date: str) -> tuple:
    """
    Attendance file: rename only, content unchanged, dated 2 days
    before the selected date.
    Return (raw_bytes, 'AttendanceReport_MMDDYYYY.xlsx', media_type, before, after).
    """
    try:
        column_count = len(_read_file(contents, filename).columns)
    except Exception:
        column_count = None

    output_filename = f"AttendanceReport_{_date_str(selected_date, offset_days=-2)}.xlsx"
    return contents, output_filename, XLSX_MEDIA_TYPE, column_count, column_count


def process_activation(contents: bytes, filename: str, selected_date: str) -> tuple:
    """
    Activation Detail Report transformations:

    1. Strip whitespace from all column names.
    2. Ensure all 32 output columns exist (add empty if missing).
    3. Reorder to the exact 32-column schema.
    4. Validate `actdate` — any non-blank value that isn't a valid date
       raises a ValueError naming the offending row(s).
    5. Return (csv_bytes, 'ActivationDetailReport_MMDDYYYY.csv', media_type, before, after).
    """
    df = _read_file(contents, filename)
    before_count = len(df.columns)
    df = df.copy()

    df.columns = [str(c).strip() for c in df.columns]

    for col in ACTIVATION_OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""

    df = df[ACTIVATION_OUTPUT_COLUMNS]

    parsed_actdate = pd.to_datetime(df["actdate"], errors="coerce")
    is_blank = df["actdate"].isna() | (df["actdate"].astype(str).str.strip() == "")
    invalid_mask = parsed_actdate.isna() & ~is_blank
    if invalid_mask.any():
        # +2: DataFrame index is 0-based and the header takes row 1 in the file
        details = [
            f"row {idx + 2}: invalid date '{df.at[idx, 'actdate']}'"
            for idx in df.index[invalid_mask]
        ]
        raise ValueError(
            "Activation Detail Report: invalid 'actdate' values — " + "; ".join(details)
        )

    after_count = len(df.columns)
    output_filename = f"ActivationDetailReport_{_date_str(selected_date)}.csv"
    return _to_csv_bytes(df), output_filename, CSV_MEDIA_TYPE, before_count, after_count
