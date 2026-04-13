# 📊 Sale Upload Portal

A full-stack application for uploading sales files, processing them per client, and downloading the result as CSV.

| Layer    | Tech              |
| -------- | ----------------- |
| Backend  | FastAPI + Pandas  |
| Frontend | Vite + React 18   |

---

## Project Structure

```
Sale Upload/
├── backend/
│   ├── main.py                  # FastAPI app (routes, CORS, etc.)
│   ├── requirements.txt         # Python dependencies
│   └── processors/              # One module per client
│       ├── __init__.py
│       ├── base.py              # Dispatcher – reads file & routes to handler
│       ├── usa_cell.py
│       ├── spiked_holding.py
│       ├── smart_con.py
│       ├── cherry_berry.py
│       ├── lets_go_wireless.py
│       ├── global_communications.py
│       ├── mobile_generation.py
│       └── evergreen_mobile.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js           # Proxy /api → localhost:8000
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── App.css
│       ├── index.css
│       └── components/
│           ├── UploadForm.jsx
│           └── UploadForm.css
│
└── README.md
```

---

## Quick Start

### 1. Backend

```bash
cd backend

# Create & activate a virtual environment (recommended)
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend runs at **http://localhost:8000**. Swagger docs at **/docs**.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at **http://localhost:5173** and proxies `/api/*` requests to the backend.

---

## How It Works

1. User selects a **Client** from the dropdown.
2. User picks a **Date** using the date picker.
3. User uploads a **.csv** or **.xlsx** file (drag-and-drop or browse).
4. Backend reads the file, runs the client-specific processor, and returns a **processed CSV** for download.

---

## Adding Client-Specific Logic

Each file in `backend/processors/` (e.g., `usa_cell.py`) contains a `process(df, selected_date)` function.  
Replace the placeholder logic with your real transformation rules:

```python
def process(df: pd.DataFrame, selected_date: str) -> pd.DataFrame:
    # Your business logic here
    ...
    return df
```

---

## Available Clients

- USA Cell
- Spiked Holding
- Smart Con (TS Mobility)
- Cherry Berry
- Lets Go Wireless
- Global Communications
- Mobile Generation Prepaid - (Via Ticket)
- Evergreen Mobile - (Via Ticket)
