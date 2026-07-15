import { useState, useEffect, useRef } from "react";
import axios from "axios";
import "./UploadForm.css";

const API_BASE = "/api";

// Clients that only accept CSV — must stay in sync with backend CSV_ONLY_CLIENTS
const CSV_ONLY_CLIENTS = new Set([
  "USA Cell - (Via Ticket)",
  "Smart Con (TS Mobility)",
  "Evergreen Mobile - (Via Ticket)",
  "Lets Go Wireless",
  "Global Communications",
  "My Wireless - (Via Ticket)",
  "AtoZ - (Via Ticket)",
]);

// Clients that only accept XLSX — must stay in sync with backend XLSX_ONLY_CLIENTS
const XLSX_ONLY_CLIENTS = new Set([
  "Cherry Berry",
  "Marnics",
  "MAA Wireless - (Via Ticket)",
]);

// Clients rendered inside the "Via Ticket" optgroup
const VIA_TICKET_CLIENTS = new Set([
  "USA Cell - (Via Ticket)",
  "Mobile Generation Prepaid - (Via Ticket)",
  "Evergreen Mobile - (Via Ticket)",
  "My Wireless - (Via Ticket)",
  "AtoZ - (Via Ticket)",
  "MAA Wireless - (Via Ticket)",
]);

// Clients shown as disabled with "(Canceled)" label
const CANCELED_CLIENTS = new Set([
  "Mobile Generation Prepaid - (Via Ticket)",
]);

// Clients that are disabled but shown without any extra label
const DISABLED_CLIENTS = new Set([
  "Mobile Generation Prepaid - (Via Ticket)",
]);

// Clients that show uploaded data as an in-page table instead of downloading
const PREVIEW_CLIENTS = new Set([
  // Cherry Berry now produces a real xlsx download — no preview clients currently
]);

// Clients that take multiple input files, each processed independently
const MULTI_FILE_CLIENTS = new Set([
  "Spiked Holding",
]);

// Spiked Holding's 4 input slots: form field key, backend endpoint slug, label, accept attr, accept label
const SPIKED_HOLDING_SLOTS = [
  { key: "sale_file", endpoint: "sale", label: "Sale File", accept: ".csv", acceptLabel: ".csv" },
  { key: "employee_file", endpoint: "employee", label: "Employee File (IDM User File)", accept: ".csv", acceptLabel: ".csv" },
  { key: "attendance_file", endpoint: "attendance", label: "Attendance File", accept: ".xlsx,.xls", acceptLabel: ".xlsx" },
  { key: "activation_file", endpoint: "activation", label: "Activation Detail Report", accept: ".csv", acceptLabel: ".csv" },
];

export default function UploadForm() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [file, setFile] = useState(null);

  // Derived: does the currently selected client require CSV only?
  const csvOnly = CSV_ONLY_CLIENTS.has(selectedClient);
  const xlsxOnly = XLSX_ONLY_CLIENTS.has(selectedClient);
  const acceptAttr = csvOnly ? ".csv" : xlsxOnly ? ".xlsx,.xls" : ".csv,.xlsx,.xls";
  const acceptLabel = csvOnly
    ? <><strong>.csv</strong></>
    : xlsxOnly
    ? <><strong>.xlsx</strong></>
    : <><strong>.csv</strong>, <strong>.xlsx</strong> or <strong>.xls</strong></>;
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [colStats, setColStats] = useState(null); // { before, after }
  const [previewData, setPreviewData] = useState(null); // { columns, rows } for preview clients
  const fileInputRef = useRef(null);

  // Multi-file clients (Spiked Holding): each slot uploads & processes on its own
  const isMultiFile = MULTI_FILE_CLIENTS.has(selectedClient);
  const [slotFiles, setSlotFiles] = useState({}); // { [slotKey]: File }
  // { [slotKey]: { state: "pending"|"uploading"|"done"|"error", filename, before_count, after_count, error } }
  const [slotStatus, setSlotStatus] = useState({});

  /* Fetch client list on mount */
  useEffect(() => {
    axios
      .get(`${API_BASE}/clients`)
      .then((res) => {
        const list = Array.isArray(res.data)
          ? res.data
          : Array.isArray(res.data?.clients)
          ? res.data.clients
          : [];
        setClients(list);
      })
      .catch(() =>
        setMessage({ type: "error", text: "Failed to load client list." })
      );
  }, []);

  /* Drag-and-drop handlers */
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setColStats(null);
    }
  };

  /* Upload & process a single Spiked Holding slot immediately */
  const uploadSlot = async (slot, fileObj, date) => {
    setSlotStatus((prev) => ({ ...prev, [slot.key]: { state: "uploading" } }));

    const formData = new FormData();
    formData.append("date", date);
    formData.append("file", fileObj);

    try {
      const response = await axios.post(
        `${API_BASE}/upload/spiked-holding/${slot.endpoint}`,
        formData,
        { responseType: "blob" }
      );

      const before = response.headers["x-column-count-before"];
      const after = response.headers["x-column-count-after"];

      const disposition = response.headers["content-disposition"];
      let filename = fileObj.name;
      if (disposition) {
        const match = disposition.match(/filename="?(.+?)"?$/);
        if (match) filename = match[1];
      }

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setSlotStatus((prev) => ({
        ...prev,
        [slot.key]: {
          state: "done",
          filename,
          before_count: before ? Number(before) : null,
          after_count: after ? Number(after) : null,
        },
      }));
    } catch (err) {
      let text = "Something went wrong while processing the file.";
      if (err.response?.data instanceof Blob) {
        try {
          const raw = await err.response.data.text();
          const json = JSON.parse(raw);
          if (json?.detail) text = json.detail;
        } catch {
          // blob wasn't JSON — keep the default message
        }
      } else if (err.response?.data?.detail) {
        text = err.response.data.detail;
      } else if (err.message) {
        text = err.message;
      }
      setSlotStatus((prev) => ({ ...prev, [slot.key]: { state: "error", error: text } }));
    }
  };

  /* Multi-file (Spiked Holding) — a file dropped into a slot uploads right away */
  const handleMultiFileChange = (slot, f) => {
    setSlotFiles((prev) => ({ ...prev, [slot.key]: f }));

    if (!selectedDate) {
      setSlotStatus((prev) => ({ ...prev, [slot.key]: { state: "pending" } }));
      setMessage({ type: "error", text: "Select a date — this file will upload automatically once it's set." });
      return;
    }

    uploadSlot(slot, f, selectedDate);
  };

  /* Once a date is chosen, any already-selected-but-pending slots upload automatically */
  useEffect(() => {
    if (!selectedDate || !isMultiFile) return;
    SPIKED_HOLDING_SLOTS.forEach((slot) => {
      const f = slotFiles[slot.key];
      if (f && slotStatus[slot.key]?.state === "pending") {
        uploadSlot(slot, f, selectedDate);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedDate, isMultiFile]);

  /* Reset entire form */
  const handleReset = () => {
    setSelectedClient("");
    setSelectedDate("");
    setFile(null);
    setColStats(null);
    setPreviewData(null);
    setSlotFiles({});
    setSlotStatus({});
    setMessage({ type: "", text: "" });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  /* Submit — no-op for multi-file clients, since each slot uploads on its own */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: "", text: "" });

    if (isMultiFile) return;

    if (!selectedClient) {
      setMessage({ type: "error", text: "Please select a client." });
      return;
    }
    if (!selectedDate) {
      setMessage({ type: "error", text: "Please select a date." });
      return;
    }
    if (!file) {
      setMessage({ type: "error", text: "Please upload a file." });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("client", selectedClient);
    formData.append("date", selectedDate);

    setLoading(true);
    setPreviewData(null);

    /* ── Preview mode (e.g. Cherry Berry) ── */
    if (PREVIEW_CLIENTS.has(selectedClient)) {
      try {
        const response = await axios.post(`${API_BASE}/preview`, formData);
        const { columns, rows, before_count, after_count } = response.data;
        setPreviewData({ columns, rows });
        setColStats({ before: before_count, after: after_count });
        setMessage({ type: "success", text: `Loaded ${rows.length} rows × ${columns.length} columns.` });
        setFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      } catch (err) {
        const text =
          err.response?.data?.detail ||
          err.message ||
          "Something went wrong while reading the file.";
        setMessage({ type: "error", text });
      } finally {
        setLoading(false);
      }
      return;
    }

    /* ── Download mode (all other clients) ── */
    try {
      const response = await axios.post(`${API_BASE}/upload`, formData, {
        responseType: "blob",
      });

      /* Read column count headers */
      const before = response.headers["x-column-count-before"];
      const after  = response.headers["x-column-count-after"];
      if (before && after) {
        setColStats({ before: Number(before), after: Number(after) });
      }

      /* Trigger browser download */
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;

      const disposition = response.headers["content-disposition"];
      let filename = "processed.csv";
      if (disposition) {
        const match = disposition.match(/filename="?(.+?)"?$/);
        if (match) filename = match[1];
      }

      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      setMessage({ type: "success", text: `File processed & downloaded as "${filename}"` });

      /* Reset file input but keep stats visible */
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (err) {
      // When responseType is "blob", error bodies are also blobs — read as text first
      let text = "Something went wrong while processing the file.";
      if (err.response?.data instanceof Blob) {
        try {
          const raw = await err.response.data.text();
          const json = JSON.parse(raw);
          if (json?.detail) text = json.detail;
        } catch {
          // blob wasn't JSON — keep the default message
        }
      } else if (err.response?.data?.detail) {
        text = err.response.data.detail;
      } else if (err.message) {
        text = err.message;
      }
      setMessage({ type: "error", text });
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      {/* Client dropdown */}
      <label className="field">
        <span className="label-text">Client</span>
        <select
          value={selectedClient}
          onChange={(e) => {
            setSelectedClient(e.target.value);
            setFile(null);
            setColStats(null);
            setPreviewData(null);
            setSlotFiles({});
            setSlotStatus({});
            setMessage({ type: "", text: "" });
            if (fileInputRef.current) fileInputRef.current.value = "";
          }}
        >
          <option value="">-- Select Client --</option>

          {/* ── Via Ticket group ── */}
          <optgroup label="Via Ticket">
            {(clients || [])
              .filter((c) => VIA_TICKET_CLIENTS.has(c))
              .map((c) =>
                DISABLED_CLIENTS.has(c) ? (
                  <option key={c} value="" disabled>
                    {c}{CANCELED_CLIENTS.has(c) ? " (Canceled)" : ""}
                  </option>
                ) : (
                  <option key={c} value={c}>
                    {c}
                  </option>
                )
              )}
          </optgroup>

          {/* ── Other clients ── */}
          <optgroup label="Other">
            {(clients || [])
              .filter((c) => !VIA_TICKET_CLIENTS.has(c))
              .map((c) =>
                DISABLED_CLIENTS.has(c) ? (
                  <option key={c} value="" disabled>
                    {c}{CANCELED_CLIENTS.has(c) ? " (Canceled)" : ""}
                  </option>
                ) : (
                  <option key={c} value={c}>
                    {c}
                  </option>
                )
              )}
          </optgroup>
        </select>
      </label>

      {/* Date picker */}
      <label className="field">
        <span className="label-text">Date</span>
        <input
          type="date"
          value={selectedDate}
          onChange={(e) => setSelectedDate(e.target.value)}
        />
      </label>

      {/* File drop zone(s) */}
      {isMultiFile ? (
        <div className="multi-drop-zones">
          {SPIKED_HOLDING_SLOTS.map((slot) => (
            <MultiFileSlot
              key={slot.key}
              slot={slot}
              file={slotFiles[slot.key]}
              status={slotStatus[slot.key]}
              onChange={(f) => handleMultiFileChange(slot, f)}
            />
          ))}
        </div>
      ) : (
        <div
          className={`drop-zone ${dragActive ? "active" : ""} ${file ? "has-file" : ""}`}
          onDragEnter={handleDrag}
          onDragOver={handleDrag}
          onDragLeave={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <input
            type="file"
            accept={acceptAttr}
            ref={fileInputRef}
            onChange={handleFileChange}
            hidden
          />
          {file ? (
            <p className="file-name">📄 {file.name}</p>
          ) : (
            <p>
              Drag &amp; drop {acceptLabel} file here, or{" "}
              <span className="browse-link">browse</span>
            </p>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="form-actions">
        {!isMultiFile && (
          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? "Processing…" : "Upload & Process"}
          </button>
        )}
        <button type="button" className="reset-btn" onClick={handleReset} disabled={loading}>
          Reset
        </button>
      </div>

      {/* Column count stats */}
      {colStats && (
        <div className="col-stats">
          <div className="col-stat-box">
            <span className="col-stat-label">Columns — Original file</span>
            <span className="col-stat-value">{colStats.before}</span>
          </div>
          <div className="col-stat-arrow">→</div>
          <div className="col-stat-box processed">
            <span className="col-stat-label">Columns — Processed file</span>
            <span className="col-stat-value">{colStats.after}</span>
          </div>
        </div>
      )}

      {/* Data preview table (Cherry Berry) */}
      {previewData && (
        <div className="preview-table-wrap">
          <div className="preview-table-scroll">
            <table className="preview-table">
              <thead>
                <tr>
                  {previewData.columns.map((col, i) => (
                    <th key={i}>{col}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {previewData.rows.map((row, ri) => (
                  <tr key={ri}>
                    {row.map((cell, ci) => (
                      <td key={ci}>{cell ?? ""}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Feedback message */}
      {message.text && (
        <p className={`msg ${message.type}`}>{message.text}</p>
      )}
    </form>
  );
}

/* Single drop zone for one of Spiked Holding's 4 input slots.
   Uploads & processes automatically as soon as a file is dropped/selected. */
function MultiFileSlot({ slot, file, status, onChange }) {
  const [dragActive, setDragActive] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onChange(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      onChange(e.target.files[0]);
    }
  };

  const state = status?.state;

  return (
    <div
      className={`drop-zone multi-drop-zone ${dragActive ? "active" : ""} ${file ? "has-file" : ""} ${state === "error" ? "has-error" : ""}`}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        type="file"
        accept={slot.accept}
        ref={inputRef}
        onChange={handleFileChange}
        hidden
      />
      <p className="multi-drop-zone-label">{slot.label}</p>

      {!file && (
        <p className="multi-drop-zone-hint">
          Drag &amp; drop <strong>{slot.acceptLabel}</strong>, or{" "}
          <span className="browse-link">browse</span>
        </p>
      )}

      {file && state === "pending" && (
        <p className="multi-drop-zone-status">📄 {file.name} — waiting for date…</p>
      )}

      {file && state === "uploading" && (
        <p className="multi-drop-zone-status">⏳ Processing {file.name}…</p>
      )}

      {file && state === "done" && (
        <>
          <p className="file-name">✅ {status.filename}</p>
          {status.before_count != null && status.after_count != null && (
            <p className="multi-drop-zone-cols">{status.before_count} → {status.after_count} cols</p>
          )}
        </>
      )}

      {file && state === "error" && (
        <p className="multi-drop-zone-error">⚠ {status.error}</p>
      )}
    </div>
  );
}
