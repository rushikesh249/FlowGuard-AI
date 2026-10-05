"use client";

import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type { UploadHistoryItem, AnomalyRun } from "@/lib/types";

const REPORTS = [
  {
    key: "executive",
    title: "Executive Summary",
    description: "High-level KPIs, health score, top anomalies, and key metrics.",
    type: "upload" as const,
  },
  {
    key: "department",
    title: "Department Report",
    description: "Per-department breakdown of cases, durations, and anomaly rates.",
    type: "upload" as const,
  },
  {
    key: "anomaly",
    title: "Anomaly Report",
    description: "Complete list of flagged anomalies with AI explanations.",
    type: "run" as const,
  },
  {
    key: "monthly",
    title: "Monthly Report",
    description: "Time-series analysis: events, cases, and anomalies per month.",
    type: "upload" as const,
  },
];

export default function ReportsPage() {
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([]);
  const [selectedUpload, setSelectedUpload] = useState<number | null>(null);
  const [runs, setRuns] = useState<AnomalyRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AnomalyRun | null>(null);
  const [downloading, setDownloading] = useState<string | null>(null);

  useEffect(() => {
    api.get("/upload/history?limit=20").then((r) => {
      setUploads(r.data);
      if (r.data.length > 0) setSelectedUpload(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedUpload) return;
    api.get(`/anomaly/runs?upload_id=${selectedUpload}`).then((r) => {
      const completed = r.data.filter((run: AnomalyRun) => run.status === "completed");
      setRuns(completed);
      if (completed.length > 0) setSelectedRun(completed[0]);
    });
  }, [selectedUpload]);

  async function downloadReport(reportKey: string, type: "upload" | "run") {
    const id = type === "run" ? selectedRun?.id : selectedUpload;
    if (!id) return;

    setDownloading(reportKey);
    try {
      const path = type === "run"
        ? `/reports/anomaly/${id}?format=csv`
        : `/reports/${reportKey}/${id}?format=csv`;

      const res = await api.get(path, { responseType: "blob" });
      const filename = `${reportKey}_report.csv`;

      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Download failed:", err);
    } finally {
      setDownloading(null);
    }
  }

  return (
    <DashboardShell>
      <div className="p-6 max-w-4xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[18px] font-semibold text-slate-900">Reports</h1>
            <p className="text-[12px] text-slate-400 mt-0.5">
              Generate and download CSV reports
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedUpload ?? ""}
              onChange={(e) => setSelectedUpload(Number(e.target.value))}
              className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white"
            >
              {uploads.map((u) => (
                <option key={u.id} value={u.id}>{u.original_name}</option>
              ))}
            </select>
            {runs.length > 0 && (
              <select
                value={selectedRun?.id ?? ""}
                onChange={(e) => {
                  const r = runs.find((run) => run.id === Number(e.target.value));
                  setSelectedRun(r ?? null);
                }}
                className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white"
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    Run #{r.id} ({r.algorithm})
                  </option>
                ))}
              </select>
            )}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {REPORTS.map((report) => (
            <div
              key={report.key}
              className="bg-white border border-slate-200 rounded p-5"
            >
              <h3 className="text-[14px] font-medium text-slate-800 mb-1">
                {report.title}
              </h3>
              <p className="text-[12px] text-slate-400 mb-4 leading-relaxed">
                {report.description}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => downloadReport(report.key, report.type)}
                  disabled={
                    downloading === report.key ||
                    (report.type === "run" && !selectedRun)
                  }
                  className="px-3 py-1.5 text-[11px] font-medium bg-slate-900 text-white rounded hover:bg-slate-800 disabled:opacity-40 transition-colors"
                >
                  {downloading === report.key ? "Downloading..." : "Download CSV"}
                </button>
              </div>
            </div>
          ))}
        </div>

        {!selectedUpload && (
          <div className="mt-8 text-center py-12 text-[13px] text-slate-400">
            Upload data first to generate reports.
          </div>
        )}
      </div>
    </DashboardShell>
  );
}
