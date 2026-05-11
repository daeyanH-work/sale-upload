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
]);

export default function UploadForm() {
  const [clients, setClients] = useState([]);
  const [selectedClient, setSelectedClient] = useState("");
  const [selectedDate, setSelectedDate] = useState("");
  const [file, setFile] = useState(null);

  // Derived: does the currently selected client require CSV only?
  const csvOnly = CSV_ONLY_CLIENTS.has(selectedClient);
  const acceptAttr = csvOnly ? ".csv" : ".csv,.xlsx,.xls";
  const acceptLabel = csvOnly
    ? <><strong>.csv</strong></>
    : <><strong>.csv</strong>, <strong>.xlsx</strong> or <strong>.xls</strong></>;
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [colStats, setColStats] = useState(null); // { before, after }
  const fileInputRef = useRef(null);

  /* Fetch client list on mount */
  useEffect(() => {
    axios
      .get(`${API_BASE}/clients`)
      .then((res) => setClients(res.data.clients))
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

  /* Reset entire form */
  const handleReset = () => {
    setSelectedClient("");
    setSelectedDate("");
    setFile(null);
    setColStats(null);
    setMessage({ type: "", text: "" });
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  /* Submit */
  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ type: "", text: "" });

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
            setMessage({ type: "", text: "" });
            if (fileInputRef.current) fileInputRef.current.value = "";
          }}
        >
          <option value="">-- Select Client --</option>
          {clients.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
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

      {/* File drop zone */}
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

      {/* Actions */}
      <div className="form-actions">
        <button type="submit" className="submit-btn" disabled={loading}>
          {loading ? "Processing…" : "Upload & Process"}
        </button>
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

      {/* Feedback message */}
      {message.text && (
        <p className={`msg ${message.type}`}>{message.text}</p>
      )}
    </form>
  );
}
