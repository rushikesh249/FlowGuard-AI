"use client";

import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type {
  UploadHistoryItem,
  AnomalyRun,
  AnomalyCaseResult,
  CaseExplanation,
} from "@/lib/types";

export default function AnomaliesPage() {
  const { user } = useAuth();
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([]);
  const [selectedUpload, setSelectedUpload] = useState<number | null>(null);
  const [runs, setRuns] = useState<AnomalyRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AnomalyRun | null>(null);
  const [results, setResults] = useState<AnomalyCaseResult[]>([]);
  const [page, setPage] = useState(0);
  const [selectedCase, setSelectedCase] = useState<CaseExplanation | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const pageSize = 20;

  // Training state
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [contamination, setContamination] = useState(0.05);
  const [isTraining, setIsTraining] = useState(false);
  const [trainMessage, setTrainMessage] = useState<string | null>(null);
  const [trainError, setTrainError] = useState<string | null>(null);

  const canTrain = user?.role === "Admin" || user?.role === "Manager";

  useEffect(() => {
    api.get("/upload/history?limit=20").then((r) => {
      setUploads(r.data);
      if (r.data.length > 0) setSelectedUpload(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedUpload) return;
    api.get(`/anomaly/runs?upload_id=${selectedUpload}`).then((r) => {
      setRuns(r.data);
      const completed = r.data.find((run: AnomalyRun) => run.status === "completed");
      if (completed) {
        setSelectedRun(completed);
        loadResults(completed.id);
      } else {
        setSelectedRun(null);
        setResults([]);
      }
    });
  }, [selectedUpload]);

  async function loadResults(runId: number) {
    const res = await api.get(`/anomaly/results/${runId}?limit=1000`);
    setResults(res.data.results);
  }

  async function loadExplanation(caseId: string) {
    if (!selectedRun) return;
    setExplanationLoading(true);
    try {
      const res = await api.get(
        `/explanations/${selectedRun.id}/case/${encodeURIComponent(caseId)}`
      );
      setSelectedCase(res.data);
    } catch {
      setSelectedCase(null);
    } finally {
      setExplanationLoading(false);
    }
  }

  async function handleStartTraining() {
    if (!selectedUpload || !canTrain) return;
    setIsTraining(true);
    setTrainError(null);
    setTrainMessage("Dispatching anomaly detection task to Celery...");
    setShowTrainModal(false);

    try {
      const res = await api.post("/anomaly/train", {
        upload_id: selectedUpload,
        algorithm: "isolation_forest",
        contamination: contamination,
      });
      const runId = res.data.id;
      setTrainMessage("Extracting features & training Isolation Forest model...");

      const interval = setInterval(async () => {
        try {
          const statusRes = await api.get(`/anomaly/status/${runId}`);
          const st = statusRes.data.status;
          if (st === "completed") {
            clearInterval(interval);
            setIsTraining(false);
            setTrainMessage("Model training completed successfully!");
            const runsRes = await api.get(`/anomaly/runs?upload_id=${selectedUpload}`);
            setRuns(runsRes.data);
            const newRun = runsRes.data.find((r: AnomalyRun) => r.id === runId) || runsRes.data[0];
            setSelectedRun(newRun);
            loadResults(runId);
            setTimeout(() => setTrainMessage(null), 6000);
          } else if (st === "failed") {
            clearInterval(interval);
            setIsTraining(false);
            setTrainError(statusRes.data.error_message || "Training task failed.");
          } else {
            setTrainMessage("Training Isolation Forest on 251,734 cases in Celery worker...");
          }
        } catch {
          clearInterval(interval);
          setIsTraining(false);
        }
      }, 3500);
    } catch (err: unknown) {
      setIsTraining(false);
      const msg =
        err && typeof err === "object" && "response" in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : "Failed to start training.";
      setTrainError(msg || "Failed to start training.");
    }
  }

  const filtered = results.filter((r) => r.is_anomaly);
  const totalPages = Math.ceil(filtered.length / pageSize);
  const paged = filtered.slice(page * pageSize, (page + 1) * pageSize);

  return (
    <DashboardShell>
      <div className="p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[18px] font-semibold text-slate-900">
              Anomaly Center
            </h1>
            <p className="text-[12px] text-slate-400 mt-0.5">
              Detected anomalies and AI explanations
            </p>
          </div>
          <div className="flex items-center gap-3">
            <select
              value={selectedUpload ?? ""}
              onChange={(e) => setSelectedUpload(Number(e.target.value))}
              className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white text-slate-700"
            >
              {uploads.map((u) => (
                <option key={u.id} value={u.id}>{u.original_name}</option>
              ))}
            </select>

            {runs.length > 1 && (
              <select
                value={selectedRun?.id ?? ""}
                onChange={(e) => {
                  const r = runs.find((item) => item.id === Number(e.target.value));
                  if (r) {
                    setSelectedRun(r);
                    loadResults(r.id);
                  }
                }}
                className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white text-slate-700 font-mono"
              >
                {runs.map((r) => (
                  <option key={r.id} value={r.id}>
                    Run #{r.id} ({(r.contamination * 100).toFixed(0)}%) - {r.status}
                  </option>
                ))}
              </select>
            )}

            {/* Run Anomaly Detection button */}
            <button
              onClick={() => canTrain && setShowTrainModal(true)}
              disabled={!canTrain || isTraining}
              className={`px-3.5 py-1.5 text-[11px] font-medium rounded transition-all flex items-center gap-1.5 shadow-sm ${
                !canTrain
                  ? "bg-slate-100 text-slate-400 cursor-not-allowed border border-slate-200"
                  : isTraining
                  ? "bg-amber-100 text-amber-800 border border-amber-200 cursor-wait"
                  : "bg-indigo-600 text-white hover:bg-indigo-700 active:scale-[0.98]"
              }`}
              title={!canTrain ? "Requires Admin or Manager role" : "Train Isolation Forest model on dataset"}
            >
              {isTraining ? (
                <>
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 animate-ping" />
                  <span>Training...</span>
                </>
              ) : (
                <>
                  <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span>Run Detection</span>
                  {!canTrain && <span className="text-[9px] opacity-75">(Analyst)</span>}
                </>
              )}
            </button>
          </div>
        </div>

        {/* Live Training Status Banners */}
        {trainMessage && (
          <div className="mb-4 px-4 py-2.5 bg-indigo-50 border border-indigo-100 rounded-lg flex items-center justify-between text-[12px] text-indigo-800 animate-fadeIn">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
              <span>{trainMessage}</span>
            </div>
            {isTraining && (
              <span className="text-[11px] text-indigo-500 font-medium">Celery Worker Active</span>
            )}
          </div>
        )}

        {trainError && (
          <div className="mb-4 px-4 py-2.5 bg-red-50 border border-red-100 rounded-lg text-[12px] text-red-700 flex items-center justify-between">
            <span>{trainError}</span>
            <button onClick={() => setTrainError(null)} className="text-red-400 hover:text-red-600 text-[11px] underline">
              Dismiss
            </button>
          </div>
        )}

        {/* Training Configuration Modal */}
        {showTrainModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-xs p-4">
            <div className="bg-white rounded-xl shadow-2xl border border-slate-200 w-full max-w-md p-6">
              <div className="flex items-center justify-between mb-3">
                <h2 className="text-[15px] font-semibold text-slate-900">
                  Run Anomaly Detection
                </h2>
                <button
                  onClick={() => setShowTrainModal(false)}
                  className="text-slate-400 hover:text-slate-600 text-lg leading-none"
                >
                  &times;
                </button>
              </div>

              <p className="text-[12px] text-slate-500 mb-5 leading-relaxed">
                Executes an <strong>Isolation Forest</strong> algorithm on all cases in this dataset using 11 engineered features (durations, transitions, loop counts).
              </p>

              <div className="space-y-4 mb-6">
                <div>
                  <label className="block text-[11px] font-medium uppercase text-slate-500 mb-1">
                    Algorithm
                  </label>
                  <div className="px-3 py-2 bg-slate-50 border border-slate-200 rounded text-[12px] text-slate-700 font-mono">
                    isolation_forest (scikit-learn)
                  </div>
                </div>

                <div>
                  <div className="flex justify-between items-center mb-1.5">
                    <label className="text-[11px] font-medium uppercase text-slate-500">
                      Contamination Rate (Expected Anomaly %)
                    </label>
                    <span className="text-[13px] font-semibold text-indigo-600 font-mono">
                      {(contamination * 100).toFixed(1)}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0.01"
                    max="0.15"
                    step="0.005"
                    value={contamination}
                    onChange={(e) => setContamination(parseFloat(e.target.value))}
                    className="w-full h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-indigo-600"
                  />
                  <div className="flex justify-between text-[10px] text-slate-400 mt-1">
                    <span>1% (Strict)</span>
                    <span>5% (Recommended)</span>
                    <span>15% (Sensitive)</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  onClick={() => setShowTrainModal(false)}
                  className="px-3.5 py-1.5 text-[12px] font-medium text-slate-600 hover:bg-slate-100 rounded"
                >
                  Cancel
                </button>
                <button
                  onClick={handleStartTraining}
                  className="px-4 py-1.5 text-[12px] font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded shadow-sm flex items-center gap-1.5"
                >
                  Start Training Run
                </button>
              </div>
            </div>
          </div>
        )}

        {selectedRun && (
          <div className="flex gap-6 mb-4 text-[12px] text-slate-500">
            <span>
              Algorithm: <strong className="text-slate-700">{selectedRun.algorithm}</strong>
            </span>
            <span>
              Contamination: <strong className="text-slate-700">{(selectedRun.contamination * 100).toFixed(1)}%</strong>
            </span>
            <span>
              Flagged: <strong className="text-red-600">{selectedRun.n_anomalies}</strong> / {filtered.length}
            </span>
          </div>
        )}

        <div className="flex gap-4">
          {/* Table */}
          <div className={`bg-white border border-slate-200 rounded overflow-hidden ${selectedCase ? "flex-1" : "w-full"}`}>
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">Case ID</th>
                  <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">Score</th>
                  <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">Confidence</th>
                  <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">Events</th>
                  <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody>
                {paged.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="px-4 py-10 text-center text-[12px] text-slate-400">
                      {selectedRun ? "No results to display." : "Run anomaly detection first."}
                    </td>
                  </tr>
                ) : (
                  paged.map((r) => (
                    <tr
                      key={r.case_id}
                      className={`border-b border-slate-50 cursor-pointer hover:bg-slate-50/70 ${
                        selectedCase?.case_id === r.case_id ? "bg-slate-50" : ""
                      }`}
                      onClick={() => loadExplanation(r.case_id)}
                    >
                      <td className="px-4 py-2.5 text-[12px] font-mono text-slate-700">{r.case_id}</td>
                      <td className="px-4 py-2.5">
                        <ScorePill score={r.anomaly_score} />
                      </td>
                      <td className="px-4 py-2.5 text-[12px] text-slate-600 tabular-nums">
                        {(r.confidence * 100).toFixed(0)}%
                      </td>
                      <td className="px-4 py-2.5 text-[12px] text-slate-600 tabular-nums">{r.n_events}</td>
                      <td className="px-4 py-2.5">
                        <button className="text-[11px] text-slate-400 hover:text-slate-700 underline">
                          Explain
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>

            {/* Pagination */}
            {totalPages > 1 && (
              <div className="px-4 py-2.5 border-t border-slate-100 flex items-center justify-between">
                <span className="text-[11px] text-slate-400">
                  Page {page + 1} of {totalPages} ({filtered.length} results)
                </span>
                <div className="flex gap-1">
                  <button
                    disabled={page === 0}
                    onClick={() => setPage((p) => p - 1)}
                    className="px-2 py-1 text-[11px] border border-slate-200 rounded disabled:opacity-30"
                  >
                    Prev
                  </button>
                  <button
                    disabled={page >= totalPages - 1}
                    onClick={() => setPage((p) => p + 1)}
                    className="px-2 py-1 text-[11px] border border-slate-200 rounded disabled:opacity-30"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Explanation Panel */}
          {selectedCase && (
            <div className="w-96 bg-white border border-slate-200 rounded overflow-y-auto max-h-[calc(100vh-140px)]">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-[13px] font-medium text-slate-700">Explanation</h3>
                <button
                  onClick={() => setSelectedCase(null)}
                  className="text-[11px] text-slate-400 hover:text-slate-700"
                >
                  Close
                </button>
              </div>

              <div className="p-4">
                <div className="mb-3">
                  <p className="font-mono text-[12px] text-slate-700">{selectedCase.case_id}</p>
                  <p className="text-[12px] text-slate-400 mt-1">{selectedCase.summary}</p>
                </div>

                <div className="flex gap-3 mb-4">
                  <div>
                    <p className="text-[10px] uppercase text-slate-400">Score</p>
                    <p className="text-[14px] font-semibold text-slate-900 tabular-nums">
                      {(selectedCase.anomaly_score * 100).toFixed(0)}%
                    </p>
                  </div>
                  <div>
                    <p className="text-[10px] uppercase text-slate-400">Severity</p>
                    <p className="text-[14px] font-semibold text-slate-900 tabular-nums">
                      {selectedCase.severity_score}/10
                    </p>
                  </div>
                </div>

                {explanationLoading ? (
                  <p className="text-[12px] text-slate-400">Loading explanations...</p>
                ) : selectedCase.explanations.length === 0 ? (
                  <p className="text-[12px] text-slate-400">
                    No rule violations detected. Flagged by statistical model.
                  </p>
                ) : (
                  <div className="space-y-2.5">
                    {selectedCase.explanations.map((exp, i) => (
                      <div
                        key={i}
                        className={`p-2.5 rounded border ${
                          exp.severity === "high"
                            ? "border-red-100 bg-red-50/50"
                            : exp.severity === "warning"
                            ? "border-amber-100 bg-amber-50/50"
                            : "border-slate-100 bg-slate-50/50"
                        }`}
                      >
                        <div className="flex items-center gap-1.5 mb-1">
                          <SeverityDot severity={exp.severity} />
                          <span className="text-[11px] font-medium text-slate-600 font-mono">
                            {exp.rule}
                          </span>
                        </div>
                        <p className="text-[12px] text-slate-700 leading-relaxed">
                          {exp.description}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

function ScorePill({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const bg =
    score > 0.8
      ? "bg-red-50 text-red-700"
      : score > 0.5
      ? "bg-amber-50 text-amber-700"
      : "bg-slate-50 text-slate-600";
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium tabular-nums ${bg}`}>
      {pct}%
    </span>
  );
}

function SeverityDot({ severity }: { severity: string }) {
  const color =
    severity === "high" ? "bg-red-500" : severity === "warning" ? "bg-amber-400" : "bg-slate-300";
  return <span className={`inline-block w-1.5 h-1.5 rounded-full ${color}`} />;
}
