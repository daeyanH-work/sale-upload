"""
Sale Upload – FastAPI Backend
=============================
Endpoints:
    GET  /api/clients          → list of client names for the dropdown
    POST /api/upload           → upload file, process it, return CSV
    GET  /api/health           → simple health-check
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from io import StringIO

from processors import process_file

app = FastAPI(title="Sale Upload API", version="1.0.0")

# ── CORS – allow the Vite dev server ────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Client list (single source of truth) ────────────────────────────────
CLIENTS = [
    "USA Cell",
    "Spiked Holding",
    "Smart Con (TS Mobility)",
    "Cherry Berry",
    "Lets Go Wireless",
    "Global Communications",
    "Mobile Generation Prepaid - (Via Ticket)",
    "Evergreen Mobile - (Via Ticket)",
]


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
    if ext not in ("csv", "xlsx", "xls"):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Upload a .csv or .xlsx file.",
        )

    contents = await file.read()

    try:
        processed_df, download_name = process_file(contents, file.filename, client, date)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Convert DataFrame → CSV bytes for download
    buffer = StringIO()
    processed_df.to_csv(buffer, index=False)
    buffer.seek(0)

    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{download_name}"'},
    )


# ── Dev entry point ─────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
