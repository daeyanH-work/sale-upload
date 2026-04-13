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


CLIENT_HANDLERS = {
    "USA Cell": usa_cell_process,
    "Spiked Holding": spiked_holding_process,
    "Smart Con (TS Mobility)": smart_con_process,
    "Cherry Berry": cherry_berry_process,
    "Lets Go Wireless": lets_go_wireless_process,
    "Global Communications": global_communications_process,
    "Mobile Generation Prepaid - (Via Ticket)": mobile_generation_process,
    "Evergreen Mobile - (Via Ticket)": evergreen_mobile_process,
}


def _read_file(contents: bytes, filename: str) -> pd.DataFrame:
    """Read CSV or XLSX bytes into a DataFrame."""
    if filename.endswith(".csv"):
        return pd.read_csv(BytesIO(contents))
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(BytesIO(contents), engine="openpyxl")
    else:
        raise ValueError("Unsupported file type. Please upload a .csv or .xlsx file.")


def process_file(
    contents: bytes,
    filename: str,
    client: str,
    selected_date: str,
) -> pd.DataFrame:
    """
    Main entry point called by the FastAPI route.

    1. Read raw file into a DataFrame
    2. Dispatch to the correct client handler
    3. Return the processed DataFrame
    """
    df = _read_file(contents, filename)

    handler = CLIENT_HANDLERS.get(client)
    if handler is None:
        raise ValueError(f"Unknown client: {client}")

    processed_df = handler(df, selected_date)
    return processed_df
