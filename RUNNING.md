# Sale Upload Portal

An internal web tool for processing client sales files.

Staff select a client, pick a date, upload a raw sales export (CSV or XLSX), and instantly download a cleaned and reformatted output file — ready to upload into back-end systems.

Each client has its own transformation rules handled automatically on the server.

---

## Supported Clients

| Client | Input | Output | Columns | Output Filename |
|---|---|---|---|---|
| USA Cell - (Via Ticket) | CSV | CSV | 37 | `Sales_Details_MMDDYYYY.csv` |
| Smart Con (TS Mobility) | CSV | CSV | 49 | `SalesDetail_MMDDYYYY.csv` |
| Evergreen Mobile - (Via Ticket) | CSV | CSV | 12 | `MTD Sales Transaction Details (Rebiz) - MM-DD-YYYY.csv` |
| Lets Go Wireless | CSV | CSV | 48 | `SalesDetail_MMDDYYYY.csv` |
| Global Communications | CSV | CSV | 49 | `SalesDetail_MMDDYYYY.csv` |
| Cherry Berry | XLSX | XLSX | 7 | `CherryBerry_MMDDYYYY.xlsx` |
| Marnics | XLSX | XLSX | 25 | `Item Wise Sales Report MM-DD-YYYY.xlsx` |

---

## Client Details

### USA Cell - (Via Ticket)
- Drops 6 columns: `Related Receipt #`, `Related Rep ATTUID`, `Related Rep Username`, `IMEI1`, `IMEI2`, `MDR Amount`
- Splits `MS State EXEMPTION NUMBER - EXEMPTION REASON` into two columns
- Reorders to final 37-column schema

---

### Smart Con (TS Mobility)
- Renames `LocationName1` → `LocationName`, `EmployeeName1` → `EmployeeName`
- Drops the first unnamed index column (column A)
- Strips commas from `CustomerName`, `ModelNumber`
- Reorders to final 49-column schema

---

### Evergreen Mobile - (Via Ticket)
- Supports CSV files encoded in utf-8, latin-1, cp1252, or utf-8-sig
- Strips commas from `Customer` column
- Ensures all 12 output columns exist (adds blank if missing)
- Reorders to final 12-column schema

**Output columns:** `Store`, `Trans Date Time`, `Trans ID`, `Salesperson`, `Customer`, `Email`, `Trans Type`, `Qty`, `GP`, `Category`, `Action Type`, `Commission Item`

---

### Lets Go Wireless
- Removes the last row (totals row)
- Renames 22 columns (e.g. `GP ($)` → `Gp`, `PA1 Qty` → `Protech1`, `Opps` → `Ops Totals`)
- Drops rows where `Invoice I D` is null or empty
- Drops `Internet Air` and `VGA Elite` columns
- Fills remaining nulls with `0`
- Strips commas from `Customer Name`, `Model Number`, `Device Type Description`

---

### Global Communications
- Removes the last row (totals row)
- Drops rows where `Invoice ID` is null or empty
- Renames `Connected Devices` → `Connected devices`
- Strips commas from `Customer Name`, `Model Number`, `Device Type Description`
- Keeps `Internet Air` column (unlike Lets Go Wireless)

---

### Cherry Berry
Parses the **Server Daily Summary / Server Productivity** XLSX report.

- Automatically finds the store name, employee names, and data rows from the file layout
- One output row per employee per date

| Output Column | Source |
|---|---|
| Date | Date column in the report |
| Store Name | Extracted from file header |
| Employee Name | Extracted from sub-header row |
| Units Sold | Hardcoded `0` |
| GP | Sales $ value for that employee |
| Store ID | Blank |
| Employee ID | Blank |

---

### Marnics
- Pass-through reorder to 25-column schema
- Input and output are both XLSX
- Preserves all data as-is from the source file

---

## How to Use

1. Open the app in your browser
2. Select a **Client** from the dropdown
3. Choose the **Date**
4. Upload the raw sales file (drag & drop or browse)
5. Click **Upload & Process**
6. The processed file downloads automatically

---

## Built With

- **Backend:** Python · FastAPI · pandas
- **Frontend:** React · Vite
- **Server:** nginx
