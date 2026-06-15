"""
Sale Upload – FastAPI Backend
=============================
Endpoints:
    GET  /api/clients          → list of client names for the dropdown
    POST /api/upload           → upload file, process it, return CSV
    GET  /api/health           → simple health-check
"""

import base64

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
    allow_origins=["http://localhost:5170", "http://127.0.0.1:5170"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Column-Count-Before", "X-Column-Count-After", "Content-Disposition"],
)

# ── Client list (single source of truth) ────────────────────────────────
CLIENTS = [
    "USA Cell - (Via Ticket)",
    "Spiked Holding",
    "Smart Con (TS Mobility)",
    "Cherry Berry",
    "Lets Go Wireless",
    "Global Communications",
    "Mobile Generation Prepaid - (Via Ticket)",
    "Evergreen Mobile - (Via Ticket)",
    "Marnics",
    "My Wireless - (Via Ticket)",
    "AtoZ - (Via Ticket)",
    "MAA Wireless - (Via Ticket)",
]


# ── Clients that only accept CSV uploads ───────────────────────────────
CSV_ONLY_CLIENTS = {
    "USA Cell - (Via Ticket)",
    "Smart Con (TS Mobility)",
    "Evergreen Mobile - (Via Ticket)",
    "Lets Go Wireless",
    "Global Communications",
    "My Wireless - (Via Ticket)",
    "AtoZ - (Via Ticket)",
}
# ── Clients that only accept XLSX uploads ──────────────────────────
XLSX_ONLY_CLIENTS = {
    "Cherry Berry",
    "Marnics",
    "MAA Wireless - (Via Ticket)",
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
    }

    # ── XLSX output ─────────────────────────────────────────────────────
    if download_name.endswith(".xlsx"):
        if raw_bytes is not None:
            xlsx_bytes = raw_bytes
        else:
            xlsx_buffer = BytesIO()
            processed_df.to_excel(xlsx_buffer, index=False, engine="openpyxl")
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
    }


@app.post("/api/upload/spiked-holding")
async def upload_spiked_holding(
    date: str = Form(...),
    sale_file: UploadFile = File(...),
    employee_file: UploadFile = File(...),
    attendance_file: UploadFile = File(...),
    activation_file: UploadFile = File(...),
):
    """
    Spiked Holding requires all 4 files in one request
    (Sale, Employee, Attendance, Activation Detail Report) and returns
    each one processed/renamed as a separate base64-encoded result.
    """
    slots = [
        (sale_file, spiked_holding_process_sale, ("csv",), "Sale file"),
        (employee_file, spiked_holding_process_employee, ("csv",), "Employee file"),
        (attendance_file, spiked_holding_process_attendance, ("xlsx", "xls"), "Attendance file"),
        (activation_file, spiked_holding_process_activation, ("csv",), "Activation Detail Report"),
    ]

    results = []
    for upload, processor, allowed_exts, label in slots:
        if not upload.filename:
            raise HTTPException(status_code=400, detail=f"{label} is required.")

        ext = upload.filename.rsplit(".", 1)[-1].lower()
        if ext not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=f"{label} must be a .{'/.'.join(allowed_exts)} file.",
            )

        contents = await upload.read()
        try:
            data, output_filename, media_type, before_count, after_count = processor(contents, upload.filename, date)
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"{label}: {e}")

        results.append({
            "filename": output_filename,
            "media_type": media_type,
            "before_count": before_count,
            "after_count": after_count,
            "data": base64.b64encode(data).decode("ascii"),
        })

    return {"results": results}


# ── Dev entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
