import React, { useState, useCallback } from "react";
import { toast } from "react-toastify";
import {
  uploadDocument,
  getDagRunStatus,
  IngestResponse,
  DagRunStatus,
} from "../services/api";
import "./Collections.css";

const BU_OPTIONS = [
  { value: "BU1", label: "BU1 — Onboarding" },
  { value: "BU2", label: "BU2 — Sales & Maintenance" },
  { value: "BU3", label: "BU3 — Billing & Subscription" },
  { value: "BU4", label: "BU4 — Support & Fulfillment" },
  { value: "BU5", label: "BU5 — Care Operations" },
];

const SERVICE_TYPES = [
  { value: "", label: "None" },
  { value: "personal-care-companionship", label: "Personal Care & Companionship" },
  { value: "skilled-nursing", label: "Skilled Nursing" },
  { value: "physical-therapy", label: "Physical Therapy" },
  { value: "occupational-therapy", label: "Occupational Therapy" },
  { value: "respite-care", label: "Respite Care" },
];

interface IngestionRecord {
  dag_run_id: string;
  file_name: string;
  bu: string;
  file_path: string;
  status: string;
  uploaded_at: string;
}

const Collections: React.FC = () => {
  const [file, setFile] = useState<File | null>(null);
  const [bu, setBu] = useState("");
  const [customerId, setCustomerId] = useState("");
  const [serviceType, setServiceType] = useState("");
  const [loading, setLoading] = useState(false);
  const [records, setRecords] = useState<IngestionRecord[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !bu) return;

    setLoading(true);
    try {
      const result: IngestResponse = await uploadDocument(
        file,
        bu,
        customerId,
        serviceType
      );

      const newRecord: IngestionRecord = {
        dag_run_id: result.dag_run_id,
        file_name: file.name,
        bu,
        file_path: result.file_path,
        status: result.status,
        uploaded_at: new Date().toLocaleString(),
      };

      setRecords((prev) => [newRecord, ...prev]);
      toast.success(`Document uploaded successfully! DAG: ${result.dag_run_id}`);

      // Reset form
      setFile(null);
      setBu("");
      setCustomerId("");
      setServiceType("");
      const fileInput = document.getElementById("file-input") as HTMLInputElement;
      if (fileInput) fileInput.value = "";
    } catch (err: any) {
      toast.error(
        err.response?.data?.detail || "Failed to upload document. Please try again."
      );
    } finally {
      setLoading(false);
    }
  };

  const refreshStatus = useCallback(
    async (dagRunId: string) => {
      try {
        const status: DagRunStatus = await getDagRunStatus(dagRunId);
        setRecords((prev) =>
          prev.map((r) =>
            r.dag_run_id === dagRunId ? { ...r, status: status.state } : r
          )
        );
      } catch {
        toast.error(`Failed to fetch status for ${dagRunId}`);
      }
    },
    []
  );

  const getStatusBadge = (status: string) => {
    const map: Record<string, string> = {
      queued: "badge-queued",
      running: "badge-running",
      success: "badge-success",
      failed: "badge-failed",
    };
    return map[status] || "badge-queued";
  };

  return (
    <div className="collections-page">
      <h1>Collections</h1>
      <p className="page-subtitle">Ingest documents into the RAG vector store</p>

      {/* Upload Form */}
      <div className="card">
        <h2>Upload Document</h2>
        <form className="ingest-form" onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="file-input">Document (PDF, TXT, MD)</label>
              <input
                id="file-input"
                type="file"
                accept=".pdf,.txt,.md"
                onChange={handleFileChange}
                required
              />
            </div>
            <div className="form-group">
              <label htmlFor="bu-select">Business Unit</label>
              <select
                id="bu-select"
                value={bu}
                onChange={(e) => setBu(e.target.value)}
                required
              >
                <option value="">Select BU</option>
                {BU_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label htmlFor="customer-id">Customer ID (optional)</label>
              <input
                id="customer-id"
                type="text"
                placeholder="e.g. C123"
                value={customerId}
                onChange={(e) => setCustomerId(e.target.value)}
              />
            </div>
            <div className="form-group">
              <label htmlFor="service-type">Service Type (BU5 only)</label>
              <select
                id="service-type"
                value={serviceType}
                onChange={(e) => setServiceType(e.target.value)}
              >
                {SERVICE_TYPES.map((st) => (
                  <option key={st.value} value={st.value}>
                    {st.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <button type="submit" className="btn-upload" disabled={loading}>
            {loading ? "Uploading..." : "Upload & Ingest"}
          </button>
        </form>
      </div>

      {/* Ingestion History Table */}
      <div className="card" style={{ marginTop: 24 }}>
        <h2>Ingestion History</h2>
        {records.length === 0 ? (
          <p className="empty-state">No documents ingested yet in this session.</p>
        ) : (
          <table className="ingest-table">
            <thead>
              <tr>
                <th>File</th>
                <th>BU</th>
                <th>DAG Run ID</th>
                <th>Status</th>
                <th>Uploaded</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.dag_run_id}>
                  <td>{r.file_name}</td>
                  <td>{r.bu}</td>
                  <td className="dag-id">{r.dag_run_id}</td>
                  <td>
                    <span className={`badge ${getStatusBadge(r.status)}`}>
                      {r.status}
                    </span>
                  </td>
                  <td>{r.uploaded_at}</td>
                  <td>
                    <button
                      className="btn-refresh"
                      onClick={() => refreshStatus(r.dag_run_id)}
                    >
                      Refresh
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
};

export default Collections;
