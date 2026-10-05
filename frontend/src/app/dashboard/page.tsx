"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type { UploadHistoryItem, AnomalyRun, AnomalyResultsResponse } from "@/lib/types";
import {
  BarChart,
  Bar,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Cell,
  Legend,
} from "recharts";

// ── Empty State ─────────────────────────────────────────────────────────────

function EmptyState() {
  return (
    <div className="bg-white border border-slate-200 rounded p-12 text-center max-w-md mx-auto my-12 shadow-sm">
      <h3 className="text-[14px] font-semibold text-slate-800 mb-1">
        No dataset uploaded yet
      </h3>
      <p className="text-[12px] text-slate-400 mb-4">
        Upload a .xes event log file to begin process intelligence analysis.
      </p>
      <Link
        href="/upload"
        className="inline-block px-3 py-1.5 text-[12px] font-medium text-white bg-slate-900 rounded hover:bg-slate-800 transition-colors"
      >
        Upload Dataset
      </Link>
    </div>
  );
}

// ── KPI Card ────────────────────────────────────────────────────────────────

function KpiCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: "red" | "green" | "default";
}) {
  const color =
    accent === "red"
      ? "text-red-600"
      : accent === "green"
      ? "text-emerald-600"
      : "text-slate-900";

  return (
    <div className="bg-white border border-slate-200 rounded px-4 py-3.5 shadow-sm">
      <p className="text-[11px] uppercase tracking-wider text-slate-500 font-medium">
        {label}
      </p>
      <p className={`text-[22px] font-semibold mt-1 tabular-nums ${color}`}>
        {value}
      </p>
      {sub && <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>}
    </div>
  );
}

// ── Main Page ────────────────────────────────────────────────────────────────

export default function DashboardPage() {
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([]);
  const [selectedUpload, setSelectedUpload] = useState<number | null>(null);
  const [latestRun, setLatestRun] = useState<AnomalyRun | null>(null);
  const [anomalyData, setAnomalyData] = useState<AnomalyResultsResponse | null>(null);
  const [processGraph, setProcessGraph] = useState<any>(null);
  const [deptData, setDeptData] = useState<any[]>([]);
  const [monthlyData, setMonthlyData] = useState<any[]>([]);
  const [vendorData, setVendorData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedUpload) {
      loadRuns(selectedUpload);
      loadGraph(selectedUpload);
      loadTierBData(selectedUpload);
    }
  }, [selectedUpload]);

  async function loadData() {
    setLoading(true);
    try {
      const res = await api.get("/upload/history?limit=10");
      setUploads(res.data);
      if (res.data.length > 0) {
        setSelectedUpload(res.data[0].id);
      }
    } catch {
      // Will show empty state
    } finally {
      setLoading(false);
    }
  }

  async function loadRuns(uploadId: number) {
    try {
      const runsRes = await api.get(`/anomaly/runs?upload_id=${uploadId}`);
      const runs: AnomalyRun[] = runsRes.data;
      const completed = runs.find((r) => r.status === "completed");
      if (completed) {
        setLatestRun(completed);
        const resultsRes = await api.get(
          `/anomaly/results/${completed.id}?limit=1000`
        );
        setAnomalyData(resultsRes.data);
      } else {
        setLatestRun(null);
        setAnomalyData(null);
      }
    } catch {
      setLatestRun(null);
      setAnomalyData(null);
    }
  }

  async function loadGraph(uploadId: number) {
    try {
      const res = await api.get(`/process-mine/graph?upload_id=${uploadId}`);
      setProcessGraph(res.data);
    } catch {
      setProcessGraph(null);
    }
  }

  async function loadTierBData(uploadId: number) {
    try {
      const [deptRes, monthRes, vendRes] = await Promise.all([
        api.get(`/reports/data/department/${uploadId}`).catch(() => ({ data: { departments: [] } })),
        api.get(`/reports/data/monthly/${uploadId}`).catch(() => ({ data: { months: [] } })),
        api.get(`/reports/data/vendors/${uploadId}?top_n=8`).catch(() => ({ data: { vendors: [] } })),
      ]);
      setDeptData(deptRes.data.departments || []);
      setMonthlyData(monthRes.data.months || []);
      setVendorData(vendRes.data.vendors || []);
    } catch {
      setDeptData([]);
      setMonthlyData([]);
      setVendorData([]);
    }
  }

  // Compute dashboard stats
  const upload = uploads.find((u) => u.id === selectedUpload);
  const totalCases = upload?.total_traces ?? 0;
  const totalEvents = upload?.total_events ?? 0;
  const uniqueActivities = upload?.unique_activities ?? 0;
  const nAnomalies = latestRun?.n_anomalies ?? 0;
  const anomalyRate = latestRun?.anomaly_rate ?? 0;
  const normalPct = anomalyRate > 0 ? ((1 - anomalyRate) * 100).toFixed(1) : "—";
  const healthScore = anomalyRate > 0 ? Math.round((1 - anomalyRate) * 100) : null;

  // Average processing time calculation
  let avgDurationSec: number | null = null;
  if (processGraph?.edges && processGraph.edges.length > 0) {
    const edgesWithDuration = processGraph.edges.filter(
      (e: any) => typeof e.avg_duration_seconds === "number" && e.avg_duration_seconds > 0
    );
    if (edgesWithDuration.length > 0) {
      const totalWeighted = edgesWithDuration.reduce(
        (acc: number, e: any) => acc + (e.avg_duration_seconds || 0) * e.count,
        0
      );
      const totalCount = edgesWithDuration.reduce((acc: number, e: any) => acc + e.count, 0);
      avgDurationSec = totalCount > 0 ? totalWeighted / totalCount : null;
    }
  }

  const formatDuration = (sec: number | null) => {
    if (sec === null || sec === undefined) return "—";
    if (sec < 60) return `${Math.round(sec)}s`;
    if (sec < 3600) return `${(sec / 60).toFixed(1)}m`;
    if (sec < 86400) return `${(sec / 3600).toFixed(1)}h`;
    return `${(sec / 86400).toFixed(1)}d`;
  };

  // Score distribution data for chart
  const scoreDistribution = anomalyData?.results
    ? computeScoreDistribution(anomalyData.results)
    : [];

  // Approval bottleneck activity stats
  const approvalEntry = processGraph?.activity_stats
    ? Object.entries(processGraph.activity_stats).find(
        ([k]) => k.toLowerCase().includes("approve") || k.toLowerCase().includes("approval")
      )
    : null;
  const approvalActivityName = approvalEntry ? approvalEntry[0] : "Approval Step";
  const approvalStats: any = approvalEntry ? approvalEntry[1] : null;

  return (
    <DashboardShell>
      <div className="p-6 max-w-7xl">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-[18px] font-semibold text-slate-900">
              Dashboard
            </h1>
            <p className="text-[12px] text-slate-400 mt-0.5">
              Procure-to-Pay process intelligence & enterprise analytics
            </p>
          </div>
          {uploads.length > 0 && (
            <select
              value={selectedUpload ?? ""}
              onChange={(e) => setSelectedUpload(Number(e.target.value))}
              className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white text-slate-700 focus:outline-none"
            >
              {uploads.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.original_name}
                </option>
              ))}
            </select>
          )}
        </div>

        {loading ? (
          <div className="text-[13px] text-slate-400 py-20 text-center">
            Loading dashboard data...
          </div>
        ) : uploads.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {/* KPI Row (Tier A: Avg Processing Time included) */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 mb-6">
              <KpiCard
                label="Total Cases"
                value={totalCases.toLocaleString()}
                sub={`${totalEvents.toLocaleString()} events`}
              />
              <KpiCard
                label="Normal"
                value={`${normalPct}%`}
                sub={`${(totalCases - nAnomalies).toLocaleString()} cases`}
                accent="green"
              />
              <KpiCard
                label="Anomalies"
                value={nAnomalies.toLocaleString()}
                sub={latestRun ? `${(anomalyRate * 100).toFixed(1)}% flagged` : "No analysis run"}
                accent={nAnomalies > 0 ? "red" : "default"}
              />
              <KpiCard
                label="Activities"
                value={uniqueActivities}
                sub="Unique event types"
              />
              <KpiCard
                label="Avg Processing Time"
                value={formatDuration(avgDurationSec)}
                sub={avgDurationSec ? "Avg transition cycle" : "No time data"}
              />
              <KpiCard
                label="Health Score"
                value={healthScore !== null ? `${healthScore}` : "—"}
                sub={healthScore !== null ? "out of 100" : "Run analysis first"}
                accent={healthScore !== null && healthScore < 90 ? "red" : "green"}
              />
            </div>

            {/* Core Charts Row */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              <ChartCard title="Anomaly Score Distribution">
                {scoreDistribution.length > 0 ? (
                  <ResponsiveContainer width="100%" height={200}>
                    <BarChart data={scoreDistribution}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis
                        dataKey="range"
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          fontSize: 11,
                          border: "1px solid #e2e8f0",
                          borderRadius: 4,
                        }}
                      />
                      <Bar dataKey="count" radius={[2, 2, 0, 0]}>
                        {scoreDistribution.map((entry, idx) => (
                          <Cell
                            key={idx}
                            fill={entry.isAnomaly ? "#dc2626" : "#334155"}
                          />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <ChartPlaceholder text="Run anomaly detection to see distribution" />
                )}
              </ChartCard>

              <ChartCard title="Run Status & Model Metadata">
                {latestRun ? (
                  <div className="space-y-3 pt-2">
                    <InfoRow label="Algorithm" value={latestRun.algorithm} />
                    <InfoRow label="Contamination Rate" value={`${(latestRun.contamination * 100).toFixed(1)}%`} />
                    <InfoRow label="Started" value={latestRun.started_at ? new Date(latestRun.started_at).toLocaleString() : "—"} />
                    <InfoRow label="Completed" value={latestRun.completed_at ? new Date(latestRun.completed_at).toLocaleString() : "—"} />
                    <InfoRow label="Status" value={latestRun.status} />
                  </div>
                ) : (
                  <ChartPlaceholder text="No analysis runs yet" />
                )}
              </ChartCard>
            </div>

            {/* ── TIER B WIDGETS ────────────────────────────────────────────── */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6">
              
              {/* Widget 1: Monthly Trend */}
              <ChartCard title="Monthly Activity & Anomaly Trend">
                {monthlyData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={230}>
                    <AreaChart data={monthlyData}>
                      <defs>
                        <linearGradient id="eventGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#334155" stopOpacity={0.2} />
                          <stop offset="95%" stopColor="#334155" stopOpacity={0} />
                        </linearGradient>
                        <linearGradient id="anomGrad" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#dc2626" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#dc2626" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                      <XAxis
                        dataKey="month"
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <YAxis
                        tick={{ fontSize: 10, fill: "#94a3b8" }}
                        axisLine={false}
                        tickLine={false}
                      />
                      <Tooltip
                        contentStyle={{
                          fontSize: 11,
                          border: "1px solid #e2e8f0",
                          borderRadius: 4,
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: 11, paddingTop: 6 }} />
                      <Area
                        type="monotone"
                        dataKey="n_events"
                        name="Total Events"
                        stroke="#334155"
                        fillOpacity={1}
                        fill="url(#eventGrad)"
                      />
                      <Area
                        type="monotone"
                        dataKey="n_anomalies"
                        name="Flagged Anomalies"
                        stroke="#dc2626"
                        fillOpacity={1}
                        fill="url(#anomGrad)"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <ChartPlaceholder text="No monthly time-series data available" />
                )}
              </ChartCard>

              {/* Widget 2: Department Delay & Anomaly Rates */}
              <ChartCard title="Department Delay & Anomaly Rates">
                {deptData.length > 0 ? (
                  <div className="overflow-x-auto max-h-[230px] overflow-y-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-100">
                          <Th>Department / Spend Area</Th>
                          <Th>Cases</Th>
                          <Th>Avg Duration</Th>
                          <Th>Anomaly Rate</Th>
                        </tr>
                      </thead>
                      <tbody>
                        {deptData.slice(0, 6).map((d) => (
                          <tr key={d.department} className="border-b border-slate-50 hover:bg-slate-50/50">
                            <Td className="font-medium text-slate-800 truncate max-w-[150px]">
                              {d.department}
                            </Td>
                            <Td className="tabular-nums">{d.n_cases.toLocaleString()}</Td>
                            <Td className="tabular-nums">
                              {d.avg_duration_hours ? `${(d.avg_duration_hours / 24).toFixed(1)} days` : "—"}
                            </Td>
                            <Td>
                              <span
                                className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium tabular-nums ${
                                  d.anomaly_rate > 3
                                    ? "bg-red-50 text-red-700"
                                    : "bg-slate-100 text-slate-700"
                                }`}
                              >
                                {d.anomaly_rate}%
                              </span>
                            </Td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <ChartPlaceholder text="No department data available" />
                )}
              </ChartCard>

              {/* Widget 3: Top Vendors Breakdown */}
              <ChartCard title="Top Vendors by Volume & Spend">
                {vendorData.length > 0 ? (
                  <div className="overflow-x-auto max-h-[230px] overflow-y-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b border-slate-100">
                          <Th>Vendor</Th>
                          <Th>Cases</Th>
                          <Th>Spend (EUR)</Th>
                          <Th>Anomalies</Th>
                        </tr>
                      </thead>
                      <tbody>
                        {vendorData.slice(0, 6).map((v) => (
                          <tr key={v.vendor} className="border-b border-slate-50 hover:bg-slate-50/50">
                            <Td className="font-mono text-[11px] text-slate-800">
                              {v.vendor}
                            </Td>
                            <Td className="tabular-nums">{v.n_cases.toLocaleString()}</Td>
                            <Td className="tabular-nums font-mono">
                              €{v.total_spend_eur?.toLocaleString(undefined, { minimumFractionDigits: 0 })}
                            </Td>
                            <Td>
                              <span
                                className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium tabular-nums ${
                                  v.n_anomalies > 0 ? "bg-red-50 text-red-700" : "bg-emerald-50 text-emerald-700"
                                }`}
                              >
                                {v.n_anomalies} ({v.anomaly_rate}%)
                              </span>
                            </Td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <ChartPlaceholder text="No vendor breakdown available" />
                )}
              </ChartCard>

              {/* Widget 4: Approval Bottleneck Analysis */}
              <ChartCard title={`Approval Bottleneck (${approvalActivityName})`}>
                {approvalStats ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-slate-50 p-2.5 rounded border border-slate-100">
                        <p className="text-[10px] text-slate-500 uppercase font-medium">Avg Delay</p>
                        <p className="text-[14px] font-semibold text-slate-800 tabular-nums mt-0.5">
                          {formatDuration(approvalStats.avg_duration_seconds)}
                        </p>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded border border-slate-100">
                        <p className="text-[10px] text-slate-500 uppercase font-medium">90th %ile</p>
                        <p className="text-[14px] font-semibold text-slate-800 tabular-nums mt-0.5">
                          {formatDuration(approvalStats.p90_duration_seconds)}
                        </p>
                      </div>
                      <div className="bg-slate-50 p-2.5 rounded border border-slate-100">
                        <p className="text-[10px] text-slate-500 uppercase font-medium">Throughput</p>
                        <p className="text-[14px] font-semibold text-slate-800 tabular-nums mt-0.5">
                          {approvalStats.count?.toLocaleString()}
                        </p>
                      </div>
                    </div>

                    <div>
                      <p className="text-[11px] font-medium text-slate-600 mb-1.5">
                        Top Approving Resources & Approver Distribution:
                      </p>
                      <div className="space-y-1.5 max-h-[110px] overflow-y-auto pr-1">
                        {approvalStats.resource_counts &&
                          Object.entries(approvalStats.resource_counts)
                            .sort((a: any, b: any) => b[1] - a[1])
                            .slice(0, 4)
                            .map(([res, cnt]: any) => {
                              const share = Math.round((cnt / (approvalStats.count || 1)) * 100);
                              return (
                                <div key={res} className="flex items-center justify-between text-[11px]">
                                  <span className="font-mono text-slate-700">{res}</span>
                                  <div className="flex items-center gap-2">
                                    <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                      <div
                                        className="h-full bg-slate-800 rounded-full"
                                        style={{ width: `${Math.min(share, 100)}%` }}
                                      />
                                    </div>
                                    <span className="text-slate-500 tabular-nums w-12 text-right">
                                      {cnt.toLocaleString()} ({share}%)
                                    </span>
                                  </div>
                                </div>
                              );
                            })}
                      </div>
                    </div>
                  </div>
                ) : (
                  <ChartPlaceholder text="No approval bottleneck data found in process flow" />
                )}
              </ChartCard>

            </div>

            {/* Recent Anomalies Table */}
            <div className="bg-white border border-slate-200 rounded shadow-sm">
              <div className="px-4 py-3 border-b border-slate-100 flex items-center justify-between">
                <h3 className="text-[13px] font-medium text-slate-700">
                  Flagged Anomalies (Top 10 by Severity Score)
                </h3>
                <span className="text-[11px] text-slate-400">
                  {nAnomalies.toLocaleString()} total flagged
                </span>
              </div>
              {anomalyData && anomalyData.results.length > 0 ? (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <Th>Case ID</Th>
                      <Th>Anomaly Score</Th>
                      <Th>Confidence</Th>
                      <Th>Events</Th>
                      <Th>Activities</Th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalyData.results
                      .filter((r) => r.is_anomaly)
                      .slice(0, 10)
                      .map((r) => (
                        <tr key={r.case_id} className="border-b border-slate-50 hover:bg-slate-50/50">
                          <Td>
                            <span className="font-mono text-[11px] text-slate-900">{r.case_id}</span>
                          </Td>
                          <Td>
                            <ScoreBadge score={r.anomaly_score} />
                          </Td>
                          <Td className="tabular-nums">{(r.confidence * 100).toFixed(0)}%</Td>
                          <Td className="tabular-nums">{r.n_events}</Td>
                          <Td className="tabular-nums">{r.n_unique_activities}</Td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              ) : (
                <div className="px-4 py-8 text-center text-[12px] text-slate-400">
                  No anomalies detected yet. Upload data and run analysis.
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </DashboardShell>
  );
}

// ── Sub-components ───────────────────────────────────────────────────────────

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-white border border-slate-200 rounded p-4 shadow-sm">
      <h3 className="text-[12px] font-medium text-slate-500 uppercase tracking-wider mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

function ChartPlaceholder({ text }: { text: string }) {
  return (
    <div className="flex items-center justify-center h-[200px] text-[12px] text-slate-400">
      {text}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center py-0.5">
      <span className="text-[12px] text-slate-400">{label}</span>
      <span className="text-[12px] font-medium text-slate-700">{value}</span>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-500 uppercase tracking-wider">
      {children}
    </th>
  );
}

function Td({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <td className={`px-4 py-2.5 text-[12px] text-slate-700 ${className}`}>
      {children}
    </td>
  );
}

function ScoreBadge({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const bg = score > 0.8 ? "bg-red-50 text-red-700" : score > 0.5 ? "bg-amber-50 text-amber-700" : "bg-slate-50 text-slate-600";
  return (
    <span className={`inline-block px-1.5 py-0.5 rounded text-[11px] font-medium tabular-nums ${bg}`}>
      {pct}%
    </span>
  );
}

function computeScoreDistribution(results: any[]) {
  const buckets = [
    { range: "0.0-0.2", min: 0.0, max: 0.2, count: 0, isAnomaly: false },
    { range: "0.2-0.4", min: 0.2, max: 0.4, count: 0, isAnomaly: false },
    { range: "0.4-0.6", min: 0.4, max: 0.6, count: 0, isAnomaly: false },
    { range: "0.6-0.8", min: 0.6, max: 0.8, count: 0, isAnomaly: true },
    { range: "0.8-1.0", min: 0.8, max: 1.01, count: 0, isAnomaly: true },
  ];

  results.forEach((r) => {
    const s = r.anomaly_score;
    const b = buckets.find((b) => s >= b.min && s < b.max);
    if (b) b.count++;
  });

  return buckets;
}
