"use client";

import { useState, useRef, useEffect, DragEvent } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type { UploadResponse, UploadHistoryItem } from "@/lib/types";

export default function UploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResponse | null>(null);
  const [error, setError] = useState("");
  const [history, setHistory] = useState<UploadHistoryItem[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    loadHistory();
  }, []);

  async function loadHistory() {
    try {
      const res = await api.get("/upload/history?limit=20");
      setHistory(res.data);
    } catch {
      // ignore
    }
  }

  async function handleUpload() {
    if (!file) return;
    setUploading(true);
    setError("");
    setResult(null);

    const form = new FormData();
    form.append("file", file);

    try {
      const res = await api.post("/upload/xes", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(res.data);
      loadHistory();
    } catch (err: unknown) {
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Upload failed";
      setError(msg || "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files[0];
    if (f && f.name.endsWith(".xes")) {
      setFile(f);
    } else {
      setError("Only .xes files are accepted.");
    }
  }

  return (
    <DashboardShell>
      <div className="p-6 max-w-4xl">
        <h1 className="text-[18px] font-semibold text-slate-900 mb-1">
          Upload Data
        </h1>
        <p className="text-[12px] text-slate-400 mb-6">
          Upload XES event logs for process mining and anomaly detection.
        </p>

        {/* Drop zone */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer transition-colors ${
            dragOver
              ? "border-slate-400 bg-slate-50"
              : "border-slate-200 hover:border-slate-300"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".xes"
            className="hidden"
            onChange={(e) => e.target.files?.[0] && setFile(e.target.files[0])}
          />
          <p className="text-[13px] text-slate-500">
            {file ? (
              <span className="font-medium text-slate-700">{file.name}</span>
            ) : (
              <span>Drop .xes file here or click to browse</span>
            )}
          </p>
          <p className="text-[11px] text-slate-400 mt-1">
            BPI Challenge 2019 format supported
          </p>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-3 mt-4">
          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="px-4 py-2 text-[12px] font-medium text-white bg-slate-900 rounded hover:bg-slate-800 disabled:opacity-40 transition-colors"
          >
            {uploading ? "Processing..." : "Upload & Validate"}
          </button>
          {file && (
            <button
              onClick={() => {
                setFile(null);
                setResult(null);
                setError("");
              }}
              className="text-[12px] text-slate-400 hover:text-slate-600"
            >
              Clear
            </button>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="mt-4 px-3 py-2 bg-red-50 border border-red-100 rounded text-[12px] text-red-700">
            {error}
          </div>
        )}

        {/* Validation Result */}
        {result && (
          <div className="mt-6 bg-white border border-slate-200 rounded">
            <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-[13px] font-medium text-slate-700">
                Validation Result
              </h3>
              <StatusBadge status={result.status} />
            </div>
            <div className="p-4 grid grid-cols-3 gap-4">
              <Metric label="Traces / Cases" value={result.total_traces} />
              <Metric label="Total Events" value={result.total_events} />
              <Metric label="Unique Activities" value={result.unique_activities} />
            </div>
            {result.warnings.length > 0 && (
              <div className="px-4 pb-3">
                <p className="text-[11px] font-medium text-slate-500 mb-1">
                  Warnings
                </p>
                {result.warnings.slice(0, 3).map((w, i) => (
                  <p key={i} className="text-[11px] text-amber-600">
                    {w}
                  </p>
                ))}
              </div>
            )}
            {result.errors.length > 0 && (
              <div className="px-4 pb-3">
                <p className="text-[11px] font-medium text-slate-500 mb-1">
                  Errors
                </p>
                {result.errors.map((e, i) => (
                  <p key={i} className="text-[11px] text-red-600">
                    {e}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Upload History */}
        {history.length > 0 && (
          <div className="mt-8">
            <h3 className="text-[13px] font-medium text-slate-700 mb-3">
              Upload History
            </h3>
            <div className="bg-white border border-slate-200 rounded overflow-hidden">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-100">
                    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                      File
                    </th>
                    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                      Traces
                    </th>
                    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                      Events
                    </th>
                    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">
                      Date
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {history.map((h) => (
                    <tr key={h.id} className="border-b border-slate-50">
                      <td className="px-4 py-2.5 text-[12px] text-slate-700 font-mono truncate max-w-[200px]">
                        {h.original_name}
                      </td>
                      <td className="px-4 py-2.5">
                        <StatusBadge status={h.status} />
                      </td>
                      <td className="px-4 py-2.5 text-[12px] text-slate-600 tabular-nums">
                        {h.total_traces?.toLocaleString() ?? "—"}
                      </td>
                      <td className="px-4 py-2.5 text-[12px] text-slate-600 tabular-nums">
                        {h.total_events?.toLocaleString() ?? "—"}
                      </td>
                      <td className="px-4 py-2.5 text-[12px] text-slate-400">
                        {new Date(h.uploaded_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </DashboardShell>
  );
}

function StatusBadge({ status }: { status: string }) {
  const styles =
    status === "valid"
      ? "bg-emerald-50 text-emerald-700"
      : status === "invalid" || status === "error"
      ? "bg-red-50 text-red-700"
      : "bg-slate-50 text-slate-600";
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[11px] font-medium ${styles}`}>
      {status}
    </span>
  );
}

function Metric({ label, value }: { label: string; value: number | null }) {
  return (
    <div>
      <p className="text-[11px] text-slate-400 uppercase tracking-wider">
        {label}
      </p>
      <p className="text-[18px] font-semibold text-slate-900 tabular-nums mt-0.5">
        {value?.toLocaleString() ?? "—"}
      </p>
    </div>
  );
}
