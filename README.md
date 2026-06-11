# ?? Sale Upload Portal

A full-stack web application that lets staff upload raw sales files, automatically transforms them per client business rules, and downloads the cleaned output as CSV or XLSX.

| Layer    | Technology                        |
|----------|-----------------------------------|
| Backend  | Python 3.14 · FastAPI · Pandas 3  |
| Frontend | Vite 5 · React 18                 |
| Server   | nginx (production)                |

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Supported Clients](#supported-clients)
3. [Local Development (Windows)](#local-development-windows)
4. [Production Deployment (Ubuntu)](#production-deployment-ubuntu)
5. [How It Works](#how-it-works)
6. [Adding a New Client](#adding-a-new-client)
7. [API Reference](#api-reference)
8. [Troubleshooting](#troubleshooting)

---

## Project Structure

```
Sale Upload/
+-- start.bat                        # One-click launcher (Windows dev + prod)
+-- nginx.conf                       # nginx config for production
+-- README.md
¦
+-- backend/
¦   +-- main.py                      # FastAPI app — routes, CORS, validation
¦   +-- requirements.txt             # Python dependencies
¦   +-- processors/
¦       +-- __init__.py
¦       +-- base.py                  # File reader + client dispatcher
¦       +-- usa_cell.py              # 37-col CSV output
¦       +-- smart_con.py             # 49-col CSV output
¦       +-- evergreen_mobile.py      # 12-col CSV output
¦       +-- lets_go_wireless.py      # 48-col CSV output
¦       +-- global_communications.py # 49-col CSV output
¦       +-- cherry_berry.py          # XLSX ? XLSX (cash drawer report)
¦       +-- marnics.py               # XLSX ? XLSX (item sales report)
¦       +-- spiked_holding.py        # placeholder
¦       +-- mobile_generation.py     # placeholder (disabled in UI)
¦
+-- frontend/
    +-- vite.config.js               # Dev proxy /api ? localhost:8001
    +-- package.json
    +-- src/
        +-- main.jsx
        +-- App.jsx / App.css
        +-- components/
            +-- UploadForm.jsx       # Main UI component
            +-- UploadForm.css
```

---

## Supported Clients

| Client | Input | Output | Columns |
|---|---|---|---|
| USA Cell - (Via Ticket) | CSV | CSV | 37 |
| Smart Con (TS Mobility) | CSV | CSV | 49 |
| Evergreen Mobile - (Via Ticket) | CSV | CSV | 12 |
| Lets Go Wireless | CSV | CSV | 48 |
| Global Communications | CSV | CSV | 49 |
| Cherry Berry | XLSX | XLSX | 7 |
| Marnics | XLSX | XLSX | 25 |
| Spiked Holding | CSV/XLSX | — | *(pending)* |
| Mobile Generation Prepaid - (Via Ticket) | — | — | *(disabled)* |

---

## Local Development (Windows)

### Prerequisites

- Python 3.10+
- Node.js 18+
- Git (optional)

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

### Start (Dev Mode)

Double-click **`start.bat`** and choose **[1] DEV**, or run manually:

```bat
:: Terminal 1 — Backend
cd backend
venv\Scripts\activate
uvicorn main:app --reload --port 8001

:: Terminal 2 — Frontend
cd frontend
npm run dev
```

| Service  | URL                         |
|----------|-----------------------------|
| Frontend | http://localhost:5170       |
| Backend  | http://localhost:8001       |
| API Docs | http://localhost:8001/docs  |

---

## Production Deployment (Ubuntu)

### 1 — Install System Dependencies

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip python3-venv nginx nodejs npm git
```

### 2 — Upload Project

```bash
# From Windows (run in PowerShell):
scp -r "D:\Sale Upload" ubuntu@YOUR_SERVER_IP:/var/www/

# On the server:
sudo chown -R $USER:$USER "/var/www/Sale Upload"
cd "/var/www/Sale Upload"
```

### 3 — Setup Backend

```bash
cd "/var/www/Sale Upload/backend"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4 — Build Frontend

```bash
cd "/var/www/Sale Upload/frontend"
npm install
npm run build
# Output: frontend/dist/
```

### 5 — Systemd Service (FastAPI)

```bash
sudo nano /etc/systemd/system/saleupload.service
```

```ini
[Unit]
Description=Sale Upload FastAPI Backend
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/var/www/Sale Upload/backend
Environment="PATH=/var/www/Sale Upload/backend/venv/bin"
ExecStart=/var/www/Sale Upload/backend/venv/bin/uvicorn main:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable saleupload
sudo systemctl start saleupload
sudo systemctl status saleupload   # should say "active (running)"
```

### 6 — nginx Configuration

```bash
sudo nano /etc/nginx/sites-available/saleupload
```

```nginx
server {
    listen 5170;
    server_name YOUR_SERVER_IP;

    root /var/www/Sale Upload/frontend/dist;
    index index.html;

    client_max_body_size 50M;

    location /api/ {
        proxy_pass         http://127.0.0.1:8001;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
        add_header Access-Control-Expose-Headers "X-Column-Count-Before, X-Column-Count-After, Content-Disposition";
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

### 7 — Open Firewall

```bash
sudo ufw allow 5170/tcp
sudo ufw reload
```

### 8 — Verify

```bash
curl http://127.0.0.1:8001/api/health        # {"status":"ok"}
curl http://YOUR_SERVER_IP:5170              # HTML page
```

Open **`http://YOUR_SERVER_IP:5170`** in a browser.

### Redeployment

```bash
cd "/var/www/Sale Upload"
git pull

cd frontend && npm install && npm run build

sudo systemctl restart saleupload
sudo systemctl reload nginx   # only if nginx.conf changed
```

---

## How It Works

```
User selects Client + Date + File
        ?
POST /api/upload  (multipart/form-data)
        ?
base.py reads CSV or XLSX into a DataFrame
        ?
Dispatches to the matching processor (e.g. usa_cell.py)
        ?
Processor applies column renames, drops, reorders, cleans
        ?
Returns (processed_df, output_filename)
        ?
FastAPI streams CSV or XLSX back to browser as download
```

Custom response headers `X-Column-Count-Before` and `X-Column-Count-After` are used by the frontend to display the column stats panel.

---

## Adding a New Client

**1. Create the processor** — `backend/processors/my_client.py`:

```python
import pandas as pd
from datetime import datetime

OUTPUT_COLUMNS = ["Col1", "Col2", ...]

def process(df: pd.DataFrame, selected_date: str) -> tuple:
    df = df.copy()
    # ... your transformation logic ...
    dt = datetime.strptime(selected_date, "%Y-%m-%d")
    filename = f"MyClient_{dt.strftime('%m%d%Y')}.csv"
    return df[OUTPUT_COLUMNS], filename
```

**2. Register in `base.py`:**

```python
from .my_client import process as my_client_process

CLIENT_HANDLERS = {
    ...
    "My Client": my_client_process,
}
```

**3. Add to `main.py`:**

```python
CLIENTS = [..., "My Client"]

# If CSV only:
CSV_ONLY_CLIENTS = {..., "My Client"}

# If XLSX only:
XLSX_ONLY_CLIENTS = {..., "My Client"}
```

**4. Add to `FALLBACK_CLIENTS` in `UploadForm.jsx`:**

```js
const FALLBACK_CLIENTS = [
  ...
  "My Client",
];
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check ? `{"status":"ok"}` |
| `GET` | `/api/clients` | Returns list of client names |
| `POST` | `/api/upload` | Upload + process file, returns file download |
| `POST` | `/api/preview` | Upload + process, returns JSON rows |

**POST `/api/upload` form fields:**

| Field | Type | Description |
|-------|------|-------------|
| `file` | File | The CSV or XLSX file |
| `client` | string | Must match a name from `/api/clients` |
| `date` | string | Date in `YYYY-MM-DD` format |

**Response headers:**

| Header | Description |
|--------|-------------|
| `Content-Disposition` | Suggested download filename |
| `X-Column-Count-Before` | Column count of the raw input file |
| `X-Column-Count-After` | Column count of the processed output |

---

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `Failed to load client list` | API unreachable | Frontend falls back to hardcoded list — check backend is running |
| `only accepts .csv files` | Wrong file type uploaded | Use the format listed in the Supported Clients table |
| `File is not a zip file` | `.xls` sent to openpyxl | Handled automatically — xlrd is used for `.xls` |
| `could not find sub-header row` | Wrong report type for Cherry Berry | Upload the correct **Server Daily Summary** xlsx |
| Dropdown empty in production | nginx not proxying `/api/` | Check nginx config and `systemctl status saleupload` |
| Large file upload fails | nginx body size limit | Increase `client_max_body_size` in nginx.conf |

---

## Service Management (Quick Reference)

```bash
# Backend
sudo systemctl status saleupload
sudo systemctl restart saleupload
sudo journalctl -u saleupload -f       # live logs

# nginx
sudo systemctl status nginx
sudo systemctl reload nginx
sudo tail -f /var/log/nginx/error.log  # error logs
```
