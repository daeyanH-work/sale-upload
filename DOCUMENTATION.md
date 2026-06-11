# Sale Upload Portal — Full Project Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Tech Stack](#4-tech-stack)
5. [Local Development (Windows)](#5-local-development-windows)
6. [Production Deployment (Ubuntu / Linux)](#6-production-deployment-ubuntu--linux)
7. [Client Processors](#7-client-processors)
   - [USA Cell](#71-usa-cell---via-ticket)
   - [Smart Con (TS Mobility)](#72-smart-con-ts-mobility)
   - [Evergreen Mobile](#73-evergreen-mobile---via-ticket)
   - [Lets Go Wireless](#74-lets-go-wireless)
   - [Global Communications](#75-global-communications)
   - [Cherry Berry](#76-cherry-berry)
   - [Marnics](#77-marnics)
   - [Spiked Holding](#78-spiked-holding-disabled)
   - [Mobile Generation](#79-mobile-generation-prepaid-disabled)
8. [Frontend Guide](#8-frontend-guide)
9. [Backend API Reference](#9-backend-api-reference)
10. [Adding a New Client](#10-adding-a-new-client)
11. [File Encoding & Format Rules](#11-file-encoding--format-rules)
12. [Service Management](#12-service-management)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Project Overview

**Sale Upload Portal** is an internal web tool that allows staff to:

1. Select a client from a dropdown
2. Pick a date
3. Upload a raw sales export (CSV or XLSX)
4. Download a cleaned, reformatted output file ready for upload into back-end systems

Each client has its own transformation rules — column renames, drops, row filtering, and output format — all handled server-side in Python.

---

## 2. Architecture

```
Browser (React)
     |
     | HTTP (port 5170 in production via nginx)
     |
  nginx
  /       \
 /api/*    /* (static)
  |            |
FastAPI     frontend/dist/
(port 8001)
     |
  processors/
  (pandas transformations)
```

**Request flow:**
1. User fills the form and clicks **Upload & Process**
2. React sends `POST /api/upload` (multipart form: file + client + date)
3. nginx proxies `/api/` → FastAPI on port 8001
4. FastAPI validates the client and file extension
5. The matching processor reads the file into a pandas DataFrame and applies transformations
6. FastAPI streams the result back as a CSV or XLSX download
7. Browser auto-downloads the processed file

---

## 3. Project Structure

```
Sale Upload/
├── start.bat                          # Windows launcher (dev + prod)
├── nginx.conf                         # nginx config (production)
├── README.md                          # Quick-start reference
├── DOCUMENTATION.md                   # This file
│
├── backend/
│   ├── main.py                        # FastAPI app, routes, validation
│   ├── requirements.txt               # Python dependencies
│   └── processors/
│       ├── __init__.py                # Exports process_file()
│       ├── base.py                    # File reader + client dispatcher
│       ├── usa_cell.py
│       ├── smart_con.py
│       ├── evergreen_mobile.py
│       ├── lets_go_wireless.py
│       ├── global_communications.py
│       ├── cherry_berry.py
│       ├── marnics.py
│       ├── spiked_holding.py          # Placeholder (disabled)
│       └── mobile_generation.py       # Placeholder (disabled)
│
└── frontend/
    ├── vite.config.js                 # Dev server config (port 5170)
    ├── package.json
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── App.css
        └── components/
            ├── UploadForm.jsx         # Main UI component
            └── UploadForm.css
```

---

## 4. Tech Stack

| Layer     | Technology                              | Version  |
|-----------|-----------------------------------------|----------|
| Backend   | Python                                  | 3.14     |
| Backend   | FastAPI                                 | 0.135+   |
| Backend   | pandas                                  | 3.0+     |
| Backend   | openpyxl (xlsx read/write)              | 3.1+     |
| Backend   | xlrd (legacy .xls read)                 | 2.0+     |
| Backend   | uvicorn (ASGI server)                   | latest   |
| Frontend  | React                                   | 18       |
| Frontend  | Vite                                    | 5        |
| Frontend  | axios                                   | latest   |
| Server    | nginx                                   | latest   |

---

## 5. Local Development (Windows)

### Prerequisites
- Python 3.10+
- Node.js 18+

### First-Time Setup

**Backend:**
```bat
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Frontend:**
```bat
cd frontend
npm install
```

### Start Dev Server

Double-click **start.bat** and choose **[1] DEV**, or manually:

```bat
:: Terminal 1 — Backend
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8001

:: Terminal 2 — Frontend
cd frontend
npm run dev
```

| Service  | URL                        |
|----------|----------------------------|
| App      | http://localhost:5170      |
| API      | http://localhost:8001      |
| API Docs | http://localhost:8001/docs |

---

## 6. Production Deployment (Ubuntu / Linux)

### 6.1 Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx nodejs npm git
```

### 6.2 Upload Project Files

```bash
# From Windows PowerShell:
scp -r "D:\Sale Upload" ubuntu@YOUR_SERVER_IP:/var/www/

# Rename to lowercase (avoids path issues on Linux):
sudo mv "/var/www/Sale Upload" /var/www/sale-upload
sudo chown -R $USER:$USER /var/www/sale-upload
```

### 6.3 Backend Setup

```bash
cd /var/www/sale-upload/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 6.4 Frontend Build

```bash
cd /var/www/sale-upload/frontend
npm install
npm run build
# Output: /var/www/sale-upload/frontend/dist/
```

> **Note:** Never copy `node_modules` from Windows — always run `npm install` on the server so Linux sets correct execute permissions.

### 6.5 Systemd Service

```bash
sudo nano /etc/systemd/system/saleupload.service
```

```ini
[Unit]
Description=Sale Upload FastAPI Backend
After=network.target

[Service]
User=YOUR_USERNAME
WorkingDirectory=/var/www/sale-upload/backend
Environment="PATH=/var/www/sale-upload/backend/venv/bin"
ExecStart=/var/www/sale-upload/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

> Replace `YOUR_USERNAME` with the output of `whoami`.

```bash
sudo systemctl daemon-reload
sudo systemctl enable saleupload
sudo systemctl start saleupload
sudo systemctl status saleupload    # must show "active (running)"
```

### 6.6 nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/saleupload
```

```nginx
server {
    listen 5170;
    server_name YOUR_SERVER_IP;

    root /var/www/sale-upload/frontend/dist;
    index index.html;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass         http://127.0.0.1:8001;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        add_header Access-Control-Expose-Headers
            "X-Column-Count-Before, X-Column-Count-After, Content-Disposition";
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/saleupload /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx
```

### 6.7 Firewall

```bash
sudo ufw allow 5170/tcp
sudo ufw reload
```

### 6.8 Verify

```bash
curl http://127.0.0.1:8001/api/health    # {"status":"ok"}
```

Open `http://YOUR_SERVER_IP:5170` in a browser.

### 6.9 Redeployment

```bash
cd /var/www/sale-upload

# Rebuild frontend
cd frontend
npm install
npm run build

# Restart backend
sudo systemctl restart saleupload

# Reload nginx (only if nginx.conf changed)
sudo systemctl reload nginx
```

---

## 7. Client Processors

### 7.1 USA Cell - (Via Ticket)

| Property       | Value                                      |
|----------------|--------------------------------------------|
| Input format   | CSV                                        |
| Output format  | CSV                                        |
| Output columns | 37                                         |
| Output filename | `Sales_Details_MMDDYYYY.csv`             |

**Transformations:**
- Drops 6 columns: `Related Receipt #`, `Related Rep ATTUID`, `Related Rep Username`, `IMEI1`, `IMEI2`, `MDR Amount`
- Splits the `MS State EXEMPTION NUMBER - EXEMPTION REASON` column into two separate columns: `MS State EXEMPTION NUMBER` and `MS State EXEMPTION REASON`
- Reorders to final 37-column schema

---

### 7.2 Smart Con (TS Mobility)

| Property       | Value                       |
|----------------|-----------------------------|
| Input format   | CSV                         |
| Output format  | CSV                         |
| Output columns | 49                          |
| Output filename | `SalesDetail_MMDDYYYY.csv` |

**Transformations:**
- Renames `LocationName1` → `LocationName`, `EmployeeName1` → `EmployeeName`
- Drops column A (first unnamed index column)
- Strips commas from `CustomerName`, `ModelNumber`
- Reorders to final 49-column schema

---

### 7.3 Evergreen Mobile - (Via Ticket)

| Property       | Value                                                       |
|----------------|-------------------------------------------------------------|
| Input format   | CSV (supports utf-8, latin-1, cp1252, utf-8-sig encodings) |
| Output format  | CSV                                                         |
| Output columns | 12                                                          |
| Output filename | `MTD Sales Transaction Details (Rebiz) - MM-DD-YYYY.csv`  |

**Transformations:**
- Normalizes column name whitespace
- Ensures all 12 output columns exist (adds empty if missing)
- Strips commas from `Customer` column
- Reorders to final 12-column schema

**Output columns:**
`Store`, `Trans Date Time`, `Trans ID`, `Salesperson`, `Customer`, `Email`, `Trans Type`, `Qty`, `GP`, `Category`, `Action Type`, `Commission Item`

---

### 7.4 Lets Go Wireless

| Property       | Value                       |
|----------------|-----------------------------|
| Input format   | CSV                         |
| Output format  | CSV                         |
| Output columns | 48                          |
| Output filename | `SalesDetail_MMDDYYYY.csv` |

**Transformations:**
1. Validates file is not empty
2. Strips whitespace from column names
3. Removes the last row (totals row)
4. Renames 22 columns (e.g. `GP ($)` → `Gp`, `PA1 Qty` → `Protech1`, `Opps` → `Ops Totals`)
5. **Drops rows where `Invoice I D` is null, blank, `"nan"`, `"0"`, or `"null"`**
6. Drops `Internet Air` and `VGA Elite` columns
7. Fills remaining nulls with `0`
8. Strips commas from `Customer Name`, `Model Number`, `Device Type Description`
9. Adds any missing output columns as `0`
10. Reorders to final 48-column schema

---

### 7.5 Global Communications

| Property       | Value                       |
|----------------|-----------------------------|
| Input format   | CSV                         |
| Output format  | CSV                         |
| Output columns | 49                          |
| Output filename | `SalesDetail_MMDDYYYY.csv` |

**Transformations:**
1. Removes the last row (totals row)
2. **Drops rows where `Invoice ID` is null, blank, `"nan"`, `"0"`, or `"null"`**
3. Renames `Connected Devices` → `Connected devices`
4. Strips commas from `Customer Name`, `Model Number`, `Device Type Description`
5. Reorders to final 49-column schema

> Difference from Lets Go Wireless: keeps `Internet Air`, does not rename columns to abbreviated forms.

---

### 7.6 Cherry Berry

| Property       | Value                          |
|----------------|--------------------------------|
| Input format   | XLSX (Server Daily Summary)    |
| Output format  | XLSX                           |
| Output columns | 7                              |
| Output filename | `CherryBerry_MMDDYYYY.xlsx`   |

**Input file layout:**
```
Row 0  → Title: "Server Daily Summary / Server Productivity"
Row 1  → Blank
Row 2  → Start Date / End Date
Row 3  → Store name (col 0)
Row 4  → Blank
Row 5  → Employee names at cols 1, 6, 11 ...
Row 6  → Sub-headers: "Sales $" at cols 1, 6, 11 ...
Row 7+ → Data rows: date at col 0, sales values at employee cols
```

**Transformations:**
1. Prepends the pandas-consumed header row back as synthetic row 0 to restore full layout
2. Scans for the row containing `"Sales $"` in any cell → sub-header row
3. Reads employee names from the row above sub-headers (non-blank, non-"Total" cells)
4. Reads store name from col 0 of rows above employees (skips title/metadata keywords)
5. Extracts data rows by matching `MM/DD/YYYY` pattern in col 0
6. For each date × employee combination, reads the `Sales $` value at the employee's column

**Output columns:**

| Column        | Source                          |
|---------------|---------------------------------|
| Date          | Col 0 of each data row          |
| Store Name    | Extracted from file header area |
| Employee Name | Extracted from row above sub-headers |
| Units Sold    | Hardcoded `0`                   |
| GP            | Sales $ value at employee's column |
| Store ID      | Hardcoded `null` (blank)        |
| Employee ID   | Hardcoded `null` (blank)        |

---

### 7.7 Marnics

| Property       | Value                                      |
|----------------|--------------------------------------------|
| Input format   | XLSX                                       |
| Output format  | XLSX                                       |
| Output columns | 25                                         |
| Output filename | `Item Wise Sales Report MM-DD-YYYY.xlsx`  |

**Transformations:**
- Pass-through reorder to 25-column schema
- Preserves all data as-is from the input XLSX

**Output columns:**
`Store Name`, `Date`, `Invoice ID`, `Customer`, `Email Address`, `Phone Number`, `Customer Group`, `Type`, `Ticket ID`, `Created By`, `Assigned To`, `Category`, `Product Name`, `Serial`, `Color`, `Size`, `Network`, `Condition`, `Quantity`, `Total Sales`, `Discount`, `COGS`, `Net Profit`, *(+ 2 more)*

---

### 7.8 Spiked Holding *(Disabled)*

- Visible in dropdown but greyed out and unselectable
- No processor logic implemented yet

---

### 7.9 Mobile Generation Prepaid *(Disabled)*

- Visible in dropdown as **"Mobile Generation Prepaid - (Via Ticket) (Canceled)"**
- Greyed out and unselectable
- No processor logic implemented

---

## 8. Frontend Guide

### Dropdown Behaviour

| Group      | Clients                                                              |
|------------|----------------------------------------------------------------------|
| Via Ticket | USA Cell, Evergreen Mobile, Mobile Generation (disabled)            |
| Other      | Smart Con, Cherry Berry, Lets Go Wireless, Global Comm, Marnics, Spiked Holding (disabled) |

### File Type Enforcement (Frontend)

The `accept` attribute on the file input is set dynamically:

| Client type     | Accepted formats        |
|-----------------|-------------------------|
| CSV-only clients | `.csv` only            |
| XLSX-only clients | `.xlsx`, `.xls` only  |
| Others          | `.csv`, `.xlsx`, `.xls` |

### Column Stats Panel

After a successful upload, two boxes appear showing:
- **Columns — Original file** (from `X-Column-Count-Before` response header)
- **Columns — Processed file** (from `X-Column-Count-After` response header)

### Fallback Client List

`FALLBACK_CLIENTS` is hardcoded in `UploadForm.jsx`. The dropdown renders immediately on page load using this list. If the API call to `/api/clients` succeeds, it updates the list; if the API is unreachable, the hardcoded list still works.

### Error Handling

Blob responses from failed uploads are read as text → parsed as JSON → `detail` field extracted. This handles FastAPI's error format correctly even when axios uses `responseType: "blob"`.

---

## 9. Backend API Reference

### `GET /api/health`
```json
{ "status": "ok" }
```

### `GET /api/clients`
```json
{
  "clients": ["USA Cell - (Via Ticket)", "Smart Con (TS Mobility)", "..."]
}
```

### `POST /api/upload`

**Form fields:**

| Field    | Type   | Required | Description                      |
|----------|--------|----------|----------------------------------|
| `file`   | File   | Yes      | The CSV or XLSX to process       |
| `client` | string | Yes      | Must match a name from `/api/clients` |
| `date`   | string | Yes      | Format: `YYYY-MM-DD`             |

**Success response:**
- Binary file stream (CSV or XLSX)
- `Content-Disposition: attachment; filename="..."`
- `X-Column-Count-Before: N`
- `X-Column-Count-After: N`

**Error response (HTTP 400 / 422):**
```json
{ "detail": "Error message here" }
```

### `POST /api/preview`
Same form fields as `/api/upload`. Returns JSON instead of a file:
```json
{
  "columns": ["Col1", "Col2"],
  "rows": [["val1", "val2"]],
  "before_count": 55,
  "after_count": 12
}
```

---

## 10. Adding a New Client

### Step 1 — Create the processor

`backend/processors/my_client.py`:

```python
import pandas as pd
from datetime import datetime

OUTPUT_COLUMNS = ["Col1", "Col2", ...]

def process(df: pd.DataFrame, selected_date: str) -> tuple:
    df = df.copy()

    # --- your transformations here ---

    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    filename = f"MyClient_{dt.strftime('%m%d%Y')}.csv"
    return df[OUTPUT_COLUMNS], filename
```

### Step 2 — Register in `base.py`

```python
from .my_client import process as my_client_process

CLIENT_HANDLERS = {
    ...
    "My Client": my_client_process,
}
```

### Step 3 — Add to `main.py`

```python
CLIENTS = [..., "My Client"]

# CSV only:
CSV_ONLY_CLIENTS = {..., "My Client"}

# XLSX only:
XLSX_ONLY_CLIENTS = {..., "My Client"}
```

### Step 4 — Add to `UploadForm.jsx`

```js
const FALLBACK_CLIENTS = [
  ...
  "My Client",
];

// If CSV only:
const CSV_ONLY_CLIENTS = new Set([..., "My Client"]);

// If XLSX only:
const XLSX_ONLY_CLIENTS = new Set([..., "My Client"]);
```

### Step 5 — Add to the correct optgroup

If it's a Via Ticket client, add to `VIA_TICKET_CLIENTS` in `UploadForm.jsx`:
```js
const VIA_TICKET_CLIENTS = new Set([..., "My Client - (Via Ticket)"]);
```

---

## 11. File Encoding & Format Rules

### CSV Encoding
The backend automatically tries these encodings in order:
1. `utf-8`
2. `latin-1`
3. `cp1252`
4. `utf-8-sig`

This handles files exported from Windows Excel which commonly contain `latin-1` characters (e.g. byte `0xa0` non-breaking space).

### XLSX vs XLS
- `.xlsx` files → read with `openpyxl` engine
- `.xls` files (legacy) → read with `xlrd` engine
- `.csv` files → read with pandas CSV parser

### Client File Format Requirements

| Client                              | Input  | Output |
|-------------------------------------|--------|--------|
| USA Cell - (Via Ticket)             | CSV    | CSV    |
| Smart Con (TS Mobility)             | CSV    | CSV    |
| Evergreen Mobile - (Via Ticket)     | CSV    | CSV    |
| Lets Go Wireless                    | CSV    | CSV    |
| Global Communications               | CSV    | CSV    |
| Cherry Berry                        | XLSX   | XLSX   |
| Marnics                             | XLSX   | XLSX   |

---

## 12. Service Management

### Backend (FastAPI via systemd)

```bash
sudo systemctl status saleupload       # check status
sudo systemctl start saleupload        # start
sudo systemctl stop saleupload         # stop
sudo systemctl restart saleupload      # restart
sudo journalctl -u saleupload -f       # live logs
sudo journalctl -u saleupload -n 100   # last 100 log lines
```

### nginx

```bash
sudo nginx -t                          # test config syntax
sudo systemctl status nginx            # check status
sudo systemctl reload nginx            # reload config (no downtime)
sudo systemctl restart nginx           # full restart
sudo tail -f /var/log/nginx/error.log  # error logs
sudo tail -f /var/log/nginx/access.log # access logs
```

### Ports Reference

| Port | Service         |
|------|-----------------|
| 5170 | nginx (public)  |
| 8001 | FastAPI (internal, localhost only) |

---

## 13. Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `vite: Permission denied` on server | `node_modules` copied from Windows | `rm -rf node_modules && npm install` on the server |
| `'utf-8' codec can't decode byte` | Windows-encoded CSV | Fixed in `base.py` — latin-1 fallback handles it |
| `Import xlrd failed` | xlrd not installed in venv | `pip install xlrd>=2.0.1` |
| `only accepts .csv files` | Wrong file format uploaded | Check the client's required format in Section 7 |
| `could not find sub-header row` | Wrong xlsx file for Cherry Berry | Upload the **Server Daily Summary** report |
| `Global Communications: missing expected columns` | Input file has different column names | Verify the raw file headers match the expected schema |
| Dropdown empty in browser | API unreachable | Fallback list is hardcoded — check backend is running with `systemctl status saleupload` |
| `exit-code 217/USER` in systemd | `User=ubuntu` doesn't exist on server | Change `User=` to the correct username (`whoami`) |
| `ln: failed to create symbolic link: File exists` | nginx symlink already created | Skip the `ln -s` step, run `sudo nginx -t` directly |
| `open() failed (2: No such file or directory)` in nginx | Broken symlink or wrong path in nginx.conf | Run `ls -la /etc/nginx/sites-enabled/` and remove broken symlinks |
| Large file upload fails | nginx body size limit | Increase `client_max_body_size` in nginx config |
| Invoice ID rows not filtered | `NaN` stored as string `"nan"` | Fixed — filter checks for `nan`, `none`, `null`, `""`, `0` |
