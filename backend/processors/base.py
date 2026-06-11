"""
Base processor – reads uploaded CSV / XLSX, applies client-specific
transformations, and returns a processed pandas DataFrame.

Each client has its own handler function. Add real business logic inside the
individual handler; right now every handler simply passes through the data
with a few metadata columns so the pipeline works end-to-end.
"""

import pandas as pd
from datetime import date
from io import BytesIO

# ── client handler imports ──────────────────────────────────────────────
from .usa_cell import process as usa_cell_process
from .spiked_holding import process as spiked_holding_process
from .smart_con import process as smart_con_process
from .cherry_berry import process as cherry_berry_process
from .lets_go_wireless import process as lets_go_wireless_process
from .global_communications import process as global_communications_process
from .mobile_generation import process as mobile_generation_process
from .evergreen_mobile import process as evergreen_mobile_process
from .marnics import process as marnics_process


CLIENT_HANDLERS = {
    "USA Cell - (Via Ticket)": usa_cell_process,
    "Spiked Holding": spiked_holding_process,
    "Smart Con (TS Mobility)": smart_con_process,
    "Cherry Berry": cherry_berry_process,
    "Lets Go Wireless": lets_go_wireless_process,
    "Global Communications": global_communications_process,
    "Mobile Generation Prepaid - (Via Ticket)": mobile_generation_process,
    "Evergreen Mobile - (Via Ticket)": evergreen_mobile_process,
    "Marnics": marnics_process,
}


def _read_file(contents: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or XLSX bytes into a DataFrame."""
    if filename.endswith(".csv"):
        for encoding in ("utf-8", "latin-1", "cp1252", "utf-8-sig"):
            try:
                return pd.read_csv(BytesIO(contents), encoding=encoding)
            except (UnicodeDecodeError, Exception):
                continue
        raise ValueError("Could not decode CSV file. Try saving it as UTF-8.")
    elif filename.endswith(".xlsx"):
        return pd.read_excel(BytesIO(contents), engine="openpyxl")
    elif filename.endswith(".xls"):
        return pd.read_excel(BytesIO(contents), engine="xlrd")
    else:
        raise ValueError("Unsupported file type. Please upload a .csv or .xlsx file.")


def process_file(
    contents: bytes,
    filename: str,
    client: str,
    selected_date: str,
) -> tuple:
    """
    Main entry point called by the FastAPI route.

    1. Read raw file into a DataFrame
    2. Dispatch to the correct client handler
    3. Return (processed_df, output_filename)

    Handlers may return either:
      - a plain DataFrame  → filename defaults to '<original>_processed.csv'
      - a (DataFrame, str) tuple  → the handler controls the filename

    Returns (processed_df, output_filename, before_count, raw_bytes).
    raw_bytes is the original uploaded file bytes, unchanged, for clients
    whose output must be byte-for-byte identical to the input (e.g. Marnics).
    """
    df = _read_file(contents, filename)
    before_count = len(df.columns)  # capture original column count

    handler = CLIENT_HANDLERS.get(client)
    if handler is None:
        raise ValueError(f"Unknown client: {client}")

    result = handler(df, selected_date)

    if isinstance(result, tuple):
        processed_df, output_filename = result
    else:
        processed_df = result
        safe_name = filename.rsplit(".", 1)[0]
        output_filename = f"{safe_name}_processed.csv"

    raw_bytes = contents if client == "Marnics" else None
    return processed_df, output_filename, before_count, raw_bytes
