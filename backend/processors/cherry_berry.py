"""Processor for Cherry Berry."""

import re
import pandas as pd
from datetime import datetime


def process(df: pd.DataFrame, selected_date: str) -> tuple:
    """
    Parse the Cherry Berry 'Server Daily Summary / Server Productivity' xlsx.

    Actual layout (after pandas reads row-0 as column names):
      full row[0]  → title:  'Server Daily Summary\\nServer Productivity', Unnamed...
      full row[1]  → blank
      full row[2]  → Start Date / End Date line   (cols 2-5)
      full row[3]  → Store name at col 0          e.g. '19011 CB Lake Jacksn'
      full row[4]  → blank
      full row[5]  → Employee names at col 1, 6, 11 … (every 5); last group = 'Total'
      full row[6]  → Sub-headers: 'Sales $' at col 1, 6, 11 …
      full row[7+] → Data rows: date at col 0, employee-sales at their emp col
      ...          → 'Total' row + blank rows + 'rpower' footer  (all skipped)

    Output: Date | Store Name | Employee Name | Units Sold | GP | Store ID | Employee ID
    """
    try:
        # ─ 1. Reconstruct full matrix (pandas consumed row-0 as column names) ──
        col_names_row = list(df.columns)
        full_vals = [col_names_row] + df.reset_index(drop=True).values.tolist()
        n_rows = len(full_vals)
        n_cols = len(col_names_row)

        # ─ 2. Find sub-header row — first row where ANY cell == 'Sales $' ───────
        subheader_idx = None
        for i in range(n_rows):
            row_strs = [str(v).strip() for v in full_vals[i]]
            if "Sales $" in row_strs:
                subheader_idx = i
                break

        if subheader_idx is None:
            rows_dump = "\n".join(
                f"  row[{i}]: {full_vals[i]}" for i in range(min(n_rows, 15))
            )
            raise ValueError(
                "Cherry Berry: could not find sub-header row ('Sales $' not found).\n"
                f"File has {n_rows} rows × {n_cols} cols. First rows:\n{rows_dump}"
            )

        # ─ 3. Employee names — row directly above sub-headers ───────────────────
        emp_row = full_vals[subheader_idx - 1]
        employees = []  # list of (name, col_index)
        for col in range(n_cols):
            cell = emp_row[col]
            if pd.isna(cell):
                continue
            name = str(cell).strip()
            if name and name.lower() != "total":
                employees.append((name, col))

        if not employees:
            raise ValueError("Cherry Berry: no employee names found.")

        # ─ 4. Store name — search rows above employee row for first non-blank col-0
        store_name = ""
        for i in range(subheader_idx - 2, -1, -1):
            cell = full_vals[i][0]
            if pd.notna(cell) and str(cell).strip():
                candidate = str(cell).strip()
                # Skip obvious title / metadata rows
                if not re.search(r"(daily|summary|productivity|start date|end date)",
                                 candidate, re.IGNORECASE):
                    store_name = candidate
                    break
        if not store_name:
            # Fallback: any non-blank cell in the rows before emp row
            for i in range(subheader_idx - 2, -1, -1):
                for cell in full_vals[i]:
                    if pd.notna(cell) and str(cell).strip():
                        store_name = str(cell).strip()
                        break
                if store_name:
                    break

        # ─ 5. Data rows — first cell matches MM/DD/YYYY ──────────────────────────
        date_pat = re.compile(r"^\d{1,2}/\d{1,2}/\d{4}$")
        records = []
        for i in range(subheader_idx + 1, n_rows):
            cell = str(full_vals[i][0]).strip() if pd.notna(full_vals[i][0]) else ""
            if not date_pat.match(cell):
                continue  # skip Total row, blank rows, rpower footer
            date_val = cell
            for emp_name, emp_col in employees:
                # Employee col IS the Sales $ col (date is at col 0)
                try:
                    sales = round(float(full_vals[i][emp_col]), 2)
                except (ValueError, TypeError):
                    sales = 0.0
                records.append({
                    "Date":          date_val,
                    "Store Name":    store_name,
                    "Employee Name": emp_name,
                    "Units Sold":    0,
                    "GP":            sales,
                    "Store ID":      None,
                    "Employee ID":   None,
                })

        if not records:
            raise ValueError("Cherry Berry: no data rows found.")

        out_df = pd.DataFrame(
            records,
            columns=["Date", "Store Name", "Employee Name",
                     "Units Sold", "GP", "Store ID", "Employee ID"],
        )

        # ─ 6. Build filename ──────────────────────────────────────────────────────
        try:
            dt = datetime.strptime(selected_date, "%Y-%m-%d")
            date_str = dt.strftime("%m%d%Y")
        except ValueError:
            date_str = selected_date.replace("-", "")

        filename = f"CherryBerry_{date_str}.xlsx"
        return out_df, filename

    except ValueError:
        raise
    except Exception as exc:
        import traceback
        raise RuntimeError(
            f"Cherry Berry processing failed: {exc}\n{traceback.format_exc()}"
        ) from exc


