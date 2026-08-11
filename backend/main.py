"""
Sale Upload – FastAPI Backend
=============================
Endpoints:
    GET  /api/clients          → list of client names for the dropdown
    POST /api/upload           → upload file, process it, return CSV
    GET  /api/health           → simple health-check
"""

import json

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from io import StringIO, BytesIO

from processors import (
    process_file,
    spiked_holding_process_sale,
    spiked_holding_process_employee,
    spiked_holding_process_attendance,
    spiked_holding_process_activation,
)

app = FastAPI(title="Sale Upload API", version="1.0.0")

# ── CORS – allow the Vite dev server ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    # allow_origins=["http://localhost:5170", "http://127.0.0.1:5170"],
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Column-Count-Before",
        "X-Column-Count-After",
        "X-Processing-Steps",
        "Content-Disposition",
    ],
)

# ── Client list (single source of truth) ────────────────────────────────
CLIENTS = [
    "USA Cell - (Via Ticket)",
    "Spiked Holding",
    "Smart Con (TS Mobility)",
    "Cherry Berry",
    "Lets Go Wireless",
    "Evergreen Mobile - (Via Ticket)",
    "Marnics",
    "My Wireless - (Via Ticket)",
    "AtoZ - (Via Ticket)",
    "MAA Wireless - (Via Ticket)",
    "Mobile One - (Via Ticket)",
    "ITM Wireless",
]


# ── Clients that only accept CSV uploads ───────────────────────────────
CSV_ONLY_CLIENTS = {
    "USA Cell - (Via Ticket)",
    "Smart Con (TS Mobility)",
    "Evergreen Mobile - (Via Ticket)",
    "Lets Go Wireless",
    "My Wireless - (Via Ticket)",
    "AtoZ - (Via Ticket)",
}
# ── Clients that only accept XLSX uploads ──────────────────────────
XLSX_ONLY_CLIENTS = {
    "Cherry Berry",
    "Marnics",
    "MAA Wireless - (Via Ticket)",
    "Mobile One - (Via Ticket)",
}

# ── Human-readable processing steps, shown to the user in the processing log ──
CLIENT_STEPS = {
    "USA Cell - (Via Ticket)": [
        "Stripped whitespace/stray quotes from column names",
        "Dropped 6 unwanted columns (Related Receipt #, Related Rep ATTUID, etc.)",
        "Split 'MS State EXEMPTION NUMBER - EXEMPTION REASON' into 2 columns",
        "Reordered to the 37-column schema",
        "Converted Net Profit, Quantity, Total Product Coupons to numeric (General format)",
    ],
    "Smart Con (TS Mobility)": [
        "Stripped whitespace from column names",
        "Dropped the first raw column",
        "Kept the next 49 columns",
        "Renamed LocationName1 → LocationName, EmployeeName1 → EmployeeName",
        "Removed commas from CustomerName and ModelNumber",
        "Reordered to the 49-column schema",
    ],
    "Cherry Berry": [
        "Parsed the multi-header 'Server Daily Summary' layout",
        "Located employee names and the store name",
        "Extracted per-employee sales rows by date",
        "Built Date / Store / Employee / GP output rows",
    ],
    "Lets Go Wireless": [
        "Validated the file wasn't empty",
        "Stripped whitespace from column names",
        "Removed the totals row",
        "Renamed columns per mapping",
        "Dropped Internet Air and VGA Elite columns",
        "Replaced nulls with 0",
        "Removed commas from Customer Name, Model Number, Device Type Description",
        "Reordered to the 48-column schema",
    ],
    "Evergreen Mobile - (Via Ticket)": [
        "Stripped whitespace from column names",
        "Reordered to the 12-column schema",
        "Removed commas from the Customer column",
    ],
    "Marnics": [
        "No content changes — file renamed only",
    ],
    "My Wireless - (Via Ticket)": [
        "Stripped whitespace from column names",
        "Reordered to the 40-column schema",
    ],
    "AtoZ - (Via Ticket)": [
        "Stripped whitespace from column names",
        "Reordered to the 15-column schema",
        "Removed commas from the Customer column",
    ],
    "MAA Wireless - (Via Ticket)": [
        "Stripped whitespace from column names",
        "Reordered to the 16-column schema",
        "Converted GP column to numeric",
        "Replaced blank Tax values with 0",
        "Kept Trans Date Time as M/D/YYYY H:MM:SS AM/PM",
    ],
    "Mobile One - (Via Ticket)": [
        "Stripped whitespace from column names",
        "Reordered to the 14-column schema (extra columns dropped)",
        "Dropped fully blank rows past the last data row",
        "Formatted ServiceUniversalID as text (value unchanged)",
        "Kept Date/ActDate/DeactDate/ReactDate as M/D/YYYY (not a date serial number)",
        "Kept Net Revenue in currency text form ($X.XX / ($X.XX) for negatives)",
    ],
    "ITM Wireless": [
        "Read the upload as comma-delimited data (csv or xlsx)",
        "Stripped whitespace from column names",
        "Reordered to the 16-column schema (extra columns dropped)",
        "Exported as xlsx covering month-to-date",
    ],
}

# ── Spiked Holding: per-slot processing steps ────────────────────────────
SPIKED_HOLDING_STEPS = {
    "sale": [
        "Reordered to the 48-column schema",
        "Removed commas from itmdesc",
        "Replaced non-numeric taxamount with 0",
        "Replaced non-numeric invno with 0",
        "Validated adddate as a proper date (blank if invalid)",
        "Replaced alphabetic cashpaid values with 0",
    ],
    "employee": ["No content changes — file renamed only"],
    "attendance": ["No content changes — file renamed only (dated 2 days earlier)"],
    "activation": [
        "Reordered to the 32-column schema",
        "Validated actdate — fails with the row number(s) of any invalid dates",
    ],
}

# ── Routes ──────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/clients")
async def get_clients():
    """Return the list of available clients."""
    return {"clients": CLIENTS}


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    client: str = Form(...),
    date: str = Form(...),
):
    """
    Accept a CSV / XLSX file, process it based on the selected client,
    and return the result as a downloadable CSV.
    """
    # Validate client
    if client not in CLIENTS:
        raise HTTPException(status_code=400, detail=f"Unknown client: {client}")

    # Validate file extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if client in CSV_ONLY_CLIENTS:
        if ext != "csv":
            raise HTTPException(
                status_code=400,
                detail=f"{client} only accepts .csv files.",
            )
    elif client in XLSX_ONLY_CLIENTS:
        if ext not in ("xlsx", "xls"):
            raise HTTPException(
                status_code=400,
                detail=f"{client} only accepts .xlsx files.",
            )
    else:
        if ext not in ("csv", "xlsx", "xls"):
            raise HTTPException(
                status_code=400,
                detail="Unsupported file type. Upload a .csv or .xlsx file.",
            )

    contents = await file.read()

    try:
        processed_df, download_name, before_count, raw_bytes = process_file(contents, file.filename, client, date)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    after_count = len(processed_df.columns)

    common_headers = {
        "Content-Disposition": f'attachment; filename="{download_name}"',
        "X-Column-Count-Before": str(before_count),
        "X-Column-Count-After": str(after_count),
        "X-Processing-Steps": json.dumps(CLIENT_STEPS.get(client, [])),
    }

    # ── XLSX output ─────────────────────────────────────────────────────
    if download_name.endswith(".xlsx"):
        if raw_bytes is not None:
            xlsx_bytes = raw_bytes
        else:
            sheet_name = "Sheet" if client == "MAA Wireless - (Via Ticket)" else "Sheet1"
            xlsx_buffer = BytesIO()
            processed_df.to_excel(xlsx_buffer, index=False, engine="openpyxl", sheet_name=sheet_name)
            xlsx_buffer.seek(0)
            xlsx_bytes = xlsx_buffer.getvalue()
        return StreamingResponse(
            iter([xlsx_bytes]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=common_headers,
        )

    # ── CSV output (default) ────────────────────────────────────────────
    csv_buffer = StringIO()
    processed_df.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    return StreamingResponse(
        iter([csv_buffer.getvalue()]),
        media_type="text/csv",
        headers=common_headers,
    )


@app.post("/api/preview")
async def preview_file(
    file: UploadFile = File(...),
    client: str = Form(...),
    date: str = Form(...),
):
    """
    Read an uploaded file and return its contents as JSON for in-page display.
    Used by clients like Cherry Berry that show data in the browser.
    """
    if client not in CLIENTS:
        raise HTTPException(status_code=400, detail=f"Unknown client: {client}")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a .csv or .xlsx file.",
        )

    contents = await file.read()

    try:
        processed_df, _, before_count, _ = process_file(contents, file.filename, client, date)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    after_count = len(processed_df.columns)

    # Serialise — convert to list-of-lists; replace NaN/NaT with None for valid JSON
    import math
    columns = list(processed_df.columns)
    raw_rows = processed_df.values.tolist()
    rows = [
        [None if (isinstance(v, float) and math.isnan(v)) else v for v in row]
        for row in raw_rows
    ]

    return {
        "columns": columns,
        "rows": rows,
        "before_count": before_count,
        "after_count": after_count,
        "steps": CLIENT_STEPS.get(client, []),
    }


# ── Spiked Holding: each of the 4 slots is processed independently ──────
SPIKED_HOLDING_SLOTS = {
    "sale": (spiked_holding_process_sale, ("csv",), "Sale file"),
    "employee": (spiked_holding_process_employee, ("csv",), "Employee file"),
    "attendance": (spiked_holding_process_attendance, ("xlsx", "xls"), "Attendance file"),
    "activation": (spiked_holding_process_activation, ("csv",), "Activation Detail Report"),
}


@app.post("/api/upload/spiked-holding/{slot}")
async def upload_spiked_holding_slot(
    slot: str,
    date: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Process a single Spiked Holding file slot (sale / employee /
    attendance / activation) as soon as it's uploaded, independent of
    the other 3 slots.
    """
    if slot not in SPIKED_HOLDING_SLOTS:
        raise HTTPException(status_code=400, detail=f"Unknown file slot: {slot}")

    processor, allowed_exts, label = SPIKED_HOLDING_SLOTS[slot]

    if not file.filename:
        raise HTTPException(status_code=400, detail=f"{label} is required.")

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in allowed_exts:
        raise HTTPException(
            status_code=400,
            detail=f"{label} must be a .{'/.'.join(allowed_exts)} file.",
        )

    contents = await file.read()
    try:
        data, output_filename, media_type, before_count, after_count = processor(contents, file.filename, date)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"{label}: {e}")

    headers = {
        "Content-Disposition": f'attachment; filename="{output_filename}"',
        "X-Column-Count-Before": "" if before_count is None else str(before_count),
        "X-Column-Count-After": "" if after_count is None else str(after_count),
        "X-Processing-Steps": json.dumps(SPIKED_HOLDING_STEPS.get(slot, [])),
    }
    return StreamingResponse(iter([data]), media_type=media_type, headers=headers)


# ── Dev entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
