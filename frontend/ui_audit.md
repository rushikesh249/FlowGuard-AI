# FlowGuard AI — Frontend UI Audit (Read-Only)

Generated: 2026-08-20
No code was changed during this audit.

---

## 1. File Tree (3 levels deep, excluding node_modules and .next)

```
frontend/
├── src/
│   ├── app/
│   │   ├── anomalies/
│   │   │   └── page.tsx             (295 lines)
│   │   ├── dashboard/
│   │   │   └── page.tsx             (386 lines)
│   │   ├── login/
│   │   │   └── page.tsx             (103 lines)
│   │   ├── process/
│   │   │   └── page.tsx             (290 lines)
│   │   ├── reports/
│   │   │   └── page.tsx             (173 lines)
│   │   ├── upload/
│   │   │   └── page.tsx             (265 lines)
│   │   ├── favicon.ico
│   │   ├── globals.css              (96 lines)
│   │   ├── layout.tsx               (24 lines)
│   │   └── page.tsx                 (6 lines)
│   ├── components/
│   │   ├── dashboard-shell.tsx      (49 lines)
│   │   └── sidebar.tsx              (77 lines)
│   └── lib/
│       ├── api.ts                   (40 lines)
│       ├── auth.tsx                  (84 lines)
│       └── types.ts                 (129 lines)
├── public/
│   ├── file.svg
│   ├── globe.svg
│   ├── next.svg
│   ├── vercel.svg
│   └── window.svg
├── .gitignore
├── AGENTS.md
├── CLAUDE.md
├── Dockerfile
├── README.md
├── eslint.config.mjs
├── next-env.d.ts
├── next.config.ts
├── package.json
├── package-lock.json
├── postcss.config.mjs
└── tsconfig.json
```

**Note:** There is NO `tailwind.config.js` or `tailwind.config.ts`. This project uses **Tailwind CSS v4** which uses CSS-first configuration via `@import "tailwindcss"` and `@theme` blocks in globals.css, plus the `@tailwindcss/postcss` PostCSS plugin.

---

## 2. Full File Contents — Configuration Files

### `frontend/src/app/globals.css`

```css
@import "tailwindcss";

/* ── FlowGuard AI — Professional Fintech Theme ─────────────────────────── */

:root {
  --background: #ffffff;
  --foreground: #0f172a;
}

@theme inline {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --font-sans: var(--font-inter), ui-sans-serif, system-ui, sans-serif;
}

/* ── Base ─────────────────────────────────────────────────────────────────── */

* {
  border-color: theme("colors.slate.200");
}

body {
  background: var(--background);
  color: var(--foreground);
  font-feature-settings: "cv02", "cv03", "cv04", "cv11";
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* ── Tabular numbers for data ─────────────────────────────────────────────── */

.tabular-nums {
  font-variant-numeric: tabular-nums;
}

/* ── Scrollbar — thin, subtle ─────────────────────────────────────────────── */

::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: transparent;
}

::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* ── React Flow overrides ─────────────────────────────────────────────────── */

.react-flow__node {
  font-family: var(--font-inter), sans-serif !important;
}

.react-flow__controls {
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08) !important;
  border: 1px solid #e2e8f0 !important;
  border-radius: 6px !important;
}

.react-flow__controls-button {
  border: none !important;
  border-bottom: 1px solid #f1f5f9 !important;
}

.react-flow__controls-button:hover {
  background: #f8fafc !important;
}

.react-flow__attribution {
  display: none !important;
}

/* ── Focus styles ─────────────────────────────────────────────────────────── */

input:focus,
select:focus,
button:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px #0f172a20;
}

/* ── Selection ────────────────────────────────────────────────────────────── */

::selection {
  background: #0f172a;
  color: white;
}
```

### `tailwind.config.js` / `tailwind.config.ts`

**Does not exist.** Tailwind v4 uses CSS-first configuration. All theme config is in `globals.css` via `@theme inline { ... }`.

### `frontend/postcss.config.mjs`

```js
const config = {
  plugins: {
    "@tailwindcss/postcss": {},
  },
};

export default config;
```

### `frontend/src/app/layout.tsx` (Root Layout)

```tsx
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "FlowGuard AI — Process Intelligence Platform",
  description: "AI-powered process mining and anomaly detection for enterprise financial workflows.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html lang="en" className={`${inter.variable} h-full`}>
      <body className="h-full antialiased text-slate-900 bg-white">
        {children}
      </body>
    </html>
  );
}
```

### `frontend/next.config.ts`

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
};

export default nextConfig;
```

### `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.mts"
  ],
  "exclude": ["node_modules"]
}
```

---

## 3. Full File Contents — Every Page Component

### `frontend/src/app/page.tsx` (Root Redirect)

```tsx
import { redirect } from "next/navigation";

export default function Home() {
  redirect("/dashboard");
}
```

### `frontend/src/app/login/page.tsx`

```tsx
"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";
import { useEffect } from "react";

function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (user) router.replace("/dashboard");
  }, [user, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch {
      setError("Invalid credentials. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-slate-50">
      <div className="w-full max-w-sm">
        <div className="mb-8">
          <h1 className="text-[15px] font-semibold text-slate-900 tracking-tight">
            FlowGuard AI
          </h1>
          <p className="text-[13px] text-slate-500 mt-1">
            Sign in to your account
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="you@company.com"
            />
          </div>

          <div>
            <label className="block text-[12px] font-medium text-slate-700 mb-1.5">
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-3 py-2 text-[13px] border border-slate-200 rounded bg-white focus:outline-none focus:border-slate-400 transition-colors"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-[12px] text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 text-[13px] font-medium text-white bg-slate-900 rounded hover:bg-slate-800 disabled:opacity-50 transition-colors"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-[12px] text-slate-400 text-center">
          Procure-to-Pay process intelligence platform
        </p>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <AuthProvider>
      <LoginForm />
    </AuthProvider>
  );
}
```

### `frontend/src/app/dashboard/page.tsx`

```tsx
"use client";

import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type { UploadHistoryItem, AnomalyRun, AnomalyResultsResponse } from "@/lib/types";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  Cell,
} from "recharts";

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
    <div className="bg-white border border-slate-200 rounded px-4 py-3.5">
      <p className="text-[11px] uppercase tracking-wider text-slate-400 font-medium">
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
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  useEffect(() => {
    if (selectedUpload) loadRuns(selectedUpload);
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
          `/anomaly/results/${completed.id}?limit=200`
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

  // Compute dashboard stats
  const upload = uploads.find((u) => u.id === selectedUpload);
  const totalCases = upload?.total_traces ?? 0;
  const totalEvents = upload?.total_events ?? 0;
  const uniqueActivities = upload?.unique_activities ?? 0;
  const nAnomalies = latestRun?.n_anomalies ?? 0;
  const anomalyRate = latestRun?.anomaly_rate ?? 0;
  const normalPct = anomalyRate > 0 ? ((1 - anomalyRate) * 100).toFixed(1) : "—";
  const healthScore = anomalyRate > 0 ? Math.round((1 - anomalyRate) * 100) : null;

  // Score distribution data for chart
  const scoreDistribution = anomalyData?.results
    ? computeScoreDistribution(anomalyData.results)
    : [];

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
              Process intelligence overview
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
            Loading...
          </div>
        ) : uploads.length === 0 ? (
          <EmptyState />
        ) : (
          <>
            {/* KPI Row */}
            <div className="grid grid-cols-5 gap-3 mb-6">
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
                label="Health Score"
                value={healthScore !== null ? `${healthScore}` : "—"}
                sub={healthScore !== null ? "out of 100" : "Run analysis first"}
                accent={healthScore !== null && healthScore < 90 ? "red" : "green"}
              />
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-3 mb-6">
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

              <ChartCard title="Run Status">
                {latestRun ? (
                  <div className="space-y-3 pt-2">
                    <InfoRow label="Algorithm" value={latestRun.algorithm} />
                    <InfoRow label="Contamination" value={`${(latestRun.contamination * 100).toFixed(1)}%`} />
                    <InfoRow label="Started" value={latestRun.started_at ? new Date(latestRun.started_at).toLocaleString() : "—"} />
                    <InfoRow label="Completed" value={latestRun.completed_at ? new Date(latestRun.completed_at).toLocaleString() : "—"} />
                    <InfoRow label="Status" value={latestRun.status} />
                  </div>
                ) : (
                  <ChartPlaceholder text="No analysis runs yet" />
                )}
              </ChartCard>
            </div>

            {/* Recent Anomalies Table */}
            <div className="bg-white border border-slate-200 rounded">
              <div className="px-4 py-3 border-b border-slate-100">
                <h3 className="text-[13px] font-medium text-slate-700">
                  Top Anomalies
                </h3>
              </div>
              {anomalyData && anomalyData.results.length > 0 ? (
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-100">
                      <Th>Case ID</Th>
                      <Th>Score</Th>
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
                            <span className="font-mono text-[11px]">{r.case_id}</span>
                          </Td>
                          <Td>
                            <ScoreBadge score={r.anomaly_score} />
                          </Td>
                          <Td>{(r.confidence * 100).toFixed(0)}%</Td>
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
    <div className="bg-white border border-slate-200 rounded p-4">
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
    <div className="flex justify-between items-center">
      <span className="text-[12px] text-slate-400">{label}</span>
      <span className="text-[12px] font-medium text-slate-700">{value}</span>
    </div>
  );
}

function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-2 text-left text-[11px] font-medium text-slate-400 uppercase tracking-wider">
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

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <p className="text-[14px] text-slate-500">No data uploaded yet</p>
      <p className="text-[12px] text-slate-400 mt-1">
        Go to Upload Data to import your first event log.
      </p>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function computeScoreDistribution(
  results: { anomaly_score: number; is_anomaly: boolean }[]
) {
  const buckets = [
    { range: "0-10", min: 0, max: 0.1, count: 0, isAnomaly: false },
    { range: "10-20", min: 0.1, max: 0.2, count: 0, isAnomaly: false },
    { range: "20-30", min: 0.2, max: 0.3, count: 0, isAnomaly: false },
    { range: "30-40", min: 0.3, max: 0.4, count: 0, isAnomaly: false },
    { range: "40-50", min: 0.4, max: 0.5, count: 0, isAnomaly: false },
    { range: "50-60", min: 0.5, max: 0.6, count: 0, isAnomaly: false },
    { range: "60-70", min: 0.6, max: 0.7, count: 0, isAnomaly: false },
    { range: "70-80", min: 0.7, max: 0.8, count: 0, isAnomaly: false },
    { range: "80-90", min: 0.8, max: 0.9, count: 0, isAnomaly: true },
    { range: "90-100", min: 0.9, max: 1.01, count: 0, isAnomaly: true },
  ];

  for (const r of results) {
    const bucket = buckets.find(
      (b) => r.anomaly_score >= b.min && r.anomaly_score < b.max
    );
    if (bucket) bucket.count++;
  }

  return buckets;
}
```

### `frontend/src/app/upload/page.tsx`

```tsx
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
```

### `frontend/src/app/process/page.tsx`

```tsx
"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type {
  UploadHistoryItem,
  ProcessGraphResponse,
  ProcessNode,
  ProcessEdge,
} from "@/lib/types";
import {
  ReactFlow,
  Background,
  Controls,
  type Node,
  type Edge,
  MarkerType,
  useNodesState,
  useEdgesState,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

export default function ProcessPage() {
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([]);
  const [selectedUpload, setSelectedUpload] = useState<number | null>(null);
  const [graph, setGraph] = useState<ProcessGraphResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  useEffect(() => {
    api.get("/upload/history?limit=20").then((r) => {
      setUploads(r.data);
      if (r.data.length > 0) setSelectedUpload(r.data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedUpload) return;
    setLoading(true);
    api
      .get(`/process-mine/graph?upload_id=${selectedUpload}`)
      .then((r) => setGraph(r.data))
      .catch(() => setGraph(null))
      .finally(() => setLoading(false));
  }, [selectedUpload]);

  // Convert API data to React Flow nodes/edges
  const { flowNodes, flowEdges } = useMemo(() => {
    if (!graph) return { flowNodes: [], flowEdges: [] };

    const nodes: Node[] = graph.nodes.map((n, i) => ({
      id: n.id,
      data: {
        label: (
          <div className="text-center">
            <p className="text-[11px] font-medium text-slate-800 leading-tight truncate max-w-[140px]">
              {n.label}
            </p>
            <p className="text-[10px] text-slate-400 mt-0.5 tabular-nums">
              {n.count.toLocaleString()} events
            </p>
          </div>
        ),
      },
      position: { x: (i % 4) * 220 + 40, y: Math.floor(i / 4) * 120 + 40 },
      style: {
        border: n.is_start
          ? "2px solid #059669"
          : n.is_end
          ? "2px solid #dc2626"
          : "1px solid #cbd5e1",
        borderRadius: 6,
        padding: "8px 12px",
        background: n.is_start
          ? "#ecfdf5"
          : n.is_end
          ? "#fef2f2"
          : "#ffffff",
        fontSize: 11,
        width: 180,
      },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
    }));

    // Simple layout: place nodes in columns based on topological distance from start
    const startNodes = graph.nodes.filter((n) => n.is_start).map((n) => n.id);
    const adjacency: Record<string, string[]> = {};
    for (const e of graph.edges) {
      if (!adjacency[e.source]) adjacency[e.source] = [];
      adjacency[e.source].push(e.target);
    }

    const depth: Record<string, number> = {};
    const queue = startNodes.map((id) => ({ id, d: 0 }));
    while (queue.length) {
      const { id, d } = queue.shift()!;
      if (depth[id] !== undefined && depth[id] <= d) continue;
      depth[id] = d;
      for (const next of adjacency[id] || []) {
        queue.push({ id: next, d: d + 1 });
      }
    }
    // Assign unvisited nodes
    for (const n of graph.nodes) {
      if (depth[n.id] === undefined) depth[n.id] = 0;
    }

    // Group by depth for column layout
    const byDepth: Record<number, string[]> = {};
    for (const [id, d] of Object.entries(depth)) {
      if (!byDepth[d]) byDepth[d] = [];
      byDepth[d].push(id);
    }

    const posMap: Record<string, { x: number; y: number }> = {};
    for (const [d, ids] of Object.entries(byDepth)) {
      const col = Number(d);
      ids.forEach((id, row) => {
        posMap[id] = { x: col * 240 + 40, y: row * 110 + 40 };
      });
    }

    nodes.forEach((n) => {
      if (posMap[n.id]) n.position = posMap[n.id];
    });

    // Edges
    const maxCount = Math.max(...graph.edges.map((e) => e.count), 1);
    const edges: Edge[] = graph.edges.map((e) => ({
      id: `${e.source}-${e.target}`,
      source: e.source,
      target: e.target,
      label: e.count > 0 ? `${e.count.toLocaleString()}` : undefined,
      style: {
        strokeWidth: Math.max(1, (e.count / maxCount) * 4),
        stroke: "#94a3b8",
      },
      labelStyle: { fontSize: 9, fill: "#64748b" },
      markerEnd: { type: MarkerType.ArrowClosed, color: "#94a3b8" },
      animated: false,
    }));

    return { flowNodes: nodes, flowEdges: edges };
  }, [graph]);

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  useEffect(() => {
    setNodes(flowNodes);
    setEdges(flowEdges);
  }, [flowNodes, flowEdges, setNodes, setEdges]);

  const selectedStats = selectedNode && graph?.activity_stats?.[selectedNode];

  return (
    <DashboardShell>
      <div className="p-6 h-[calc(100vh-48px)] flex flex-col">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h1 className="text-[18px] font-semibold text-slate-900">
              Process View
            </h1>
            <p className="text-[12px] text-slate-400 mt-0.5">
              {graph
                ? `${graph.metadata.total_activities} activities · ${graph.metadata.total_transitions} transitions · ${graph.metadata.total_events.toLocaleString()} events`
                : "Workflow reconstruction"}
            </p>
          </div>
          <select
            value={selectedUpload ?? ""}
            onChange={(e) => setSelectedUpload(Number(e.target.value))}
            className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white"
          >
            {uploads.map((u) => (
              <option key={u.id} value={u.id}>{u.original_name}</option>
            ))}
          </select>
        </div>

        <div className="flex flex-1 gap-3 min-h-0">
          {/* Graph */}
          <div className="flex-1 bg-white border border-slate-200 rounded overflow-hidden">
            {loading ? (
              <div className="flex items-center justify-center h-full text-[13px] text-slate-400">
                Computing process graph...
              </div>
            ) : graph ? (
              <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeClick={(_, node) => setSelectedNode(node.id)}
                fitView
                proOptions={{ hideAttribution: true }}
              >
                <Background color="#e2e8f0" gap={20} />
                <Controls />
              </ReactFlow>
            ) : (
              <div className="flex items-center justify-center h-full text-[13px] text-slate-400">
                Upload data and run process mining to see the graph.
              </div>
            )}
          </div>

          {/* Activity stats sidebar */}
          {selectedNode && selectedStats && (
            <div className="w-72 bg-white border border-slate-200 rounded p-4 overflow-y-auto">
              <h3 className="text-[13px] font-medium text-slate-800 mb-3">
                {selectedNode}
              </h3>
              <div className="space-y-2.5 text-[12px]">
                <Stat label="Occurrences" value={selectedStats.count.toLocaleString()} />
                {selectedStats.avg_duration_seconds != null && (
                  <Stat
                    label="Avg Duration"
                    value={formatDuration(selectedStats.avg_duration_seconds)}
                  />
                )}
                {selectedStats.median_duration_seconds != null && (
                  <Stat
                    label="Median Duration"
                    value={formatDuration(selectedStats.median_duration_seconds)}
                  />
                )}
                {selectedStats.first_occurrence && (
                  <Stat label="First Seen" value={new Date(selectedStats.first_occurrence).toLocaleDateString()} />
                )}
                {selectedStats.last_occurrence && (
                  <Stat label="Last Seen" value={new Date(selectedStats.last_occurrence).toLocaleDateString()} />
                )}
                {selectedStats.departments.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase text-slate-400 mb-1">Departments</p>
                    <div className="flex flex-wrap gap-1">
                      {selectedStats.departments.slice(0, 5).map((d) => (
                        <span key={d} className="px-1.5 py-0.5 bg-slate-50 border border-slate-200 rounded text-[10px] text-slate-600">
                          {d}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {selectedStats.resources.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase text-slate-400 mb-1">
                      Resources ({selectedStats.resources.length})
                    </p>
                    <p className="text-[11px] text-slate-500">
                      {selectedStats.resources.slice(0, 3).join(", ")}
                      {selectedStats.resources.length > 3 && ` +${selectedStats.resources.length - 3} more`}
                    </p>
                  </div>
                )}
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="mt-4 text-[11px] text-slate-400 hover:text-slate-700"
              >
                Deselect
              </button>
            </div>
          )}
        </div>
      </div>
    </DashboardShell>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between">
      <span className="text-slate-400">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}

function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  if (seconds < 3600) return `${(seconds / 60).toFixed(1)}m`;
  if (seconds < 86400) return `${(seconds / 3600).toFixed(1)}h`;
  return `${(seconds / 86400).toFixed(1)}d`;
}
```

### `frontend/src/app/anomalies/page.tsx`

```tsx
"use client";

import { useEffect, useState } from "react";
import DashboardShell from "@/components/dashboard-shell";
import api from "@/lib/api";
import type {
  UploadHistoryItem,
  AnomalyRun,
  AnomalyCaseResult,
  CaseExplanation,
} from "@/lib/types";

export default function AnomaliesPage() {
  const [uploads, setUploads] = useState<UploadHistoryItem[]>([]);
  const [selectedUpload, setSelectedUpload] = useState<number | null>(null);
  const [runs, setRuns] = useState<AnomalyRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AnomalyRun | null>(null);
  const [results, setResults] = useState<AnomalyCaseResult[]>([]);
  const [page, setPage] = useState(0);
  const [selectedCase, setSelectedCase] = useState<CaseExplanation | null>(null);
  const [explanationLoading, setExplanationLoading] = useState(false);
  const [filter, setFilter] = useState<"all" | "anomalies">("anomalies");
  const pageSize = 20;

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
      }
    });
  }, [selectedUpload]);

  async function loadResults(runId: number) {
    const res = await api.get(`/anomaly/results/${runId}?limit=500`);
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

  const filtered =
    filter === "anomalies" ? results.filter((r) => r.is_anomaly) : results;
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
              className="text-[12px] border border-slate-200 rounded px-2.5 py-1.5 bg-white"
            >
              {uploads.map((u) => (
                <option key={u.id} value={u.id}>{u.original_name}</option>
              ))}
            </select>
            <div className="flex border border-slate-200 rounded overflow-hidden">
              <button
                onClick={() => { setFilter("anomalies"); setPage(0); }}
                className={`px-3 py-1.5 text-[11px] font-medium ${
                  filter === "anomalies" ? "bg-slate-900 text-white" : "bg-white text-slate-600"
                }`}
              >
                Anomalies
              </button>
              <button
                onClick={() => { setFilter("all"); setPage(0); }}
                className={`px-3 py-1.5 text-[11px] font-medium ${
                  filter === "all" ? "bg-slate-900 text-white" : "bg-white text-slate-600"
                }`}
              >
                All Cases
              </button>
            </div>
          </div>
        </div>

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
```

### `frontend/src/app/reports/page.tsx`

```tsx
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

  async function downloadReport(reportKey: string, format: "pdf" | "csv", type: "upload" | "run") {
    const id = type === "run" ? selectedRun?.id : selectedUpload;
    if (!id) return;

    setDownloading(`${reportKey}-${format}`);
    try {
      const path = type === "run"
        ? `/reports/anomaly/${id}?format=${format}`
        : `/reports/${reportKey}/${id}?format=${format}`;

      const res = await api.get(path, { responseType: "blob" });
      const ext = format === "pdf" ? "pdf" : "csv";
      const filename = `${reportKey}_report.${ext}`;

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
              Generate and download PDF or CSV reports
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
                  onClick={() => downloadReport(report.key, "pdf", report.type)}
                  disabled={
                    downloading === `${reportKey}-pdf` ||
                    (report.type === "run" && !selectedRun)
                  }
                  className="px-3 py-1.5 text-[11px] font-medium bg-slate-900 text-white rounded hover:bg-slate-800 disabled:opacity-40 transition-colors"
                >
                  {downloading === `${report.key}-pdf` ? "..." : "PDF"}
                </button>
                <button
                  onClick={() => downloadReport(report.key, "csv", report.type)}
                  disabled={
                    downloading === `${reportKey}-csv` ||
                    (report.type === "run" && !selectedRun)
                  }
                  className="px-3 py-1.5 text-[11px] font-medium border border-slate-200 text-slate-700 rounded hover:bg-slate-50 disabled:opacity-40 transition-colors"
                >
                  {downloading === `${report.key}-csv` ? "..." : "CSV"}
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
```

---

## 4. Shared Components & Library Files

### `frontend/src/components/sidebar.tsx`

```tsx
/**
 * Sidebar navigation — minimal, professional fintech aesthetic.
 */
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "□" },
  { href: "/upload", label: "Upload Data", icon: "↑" },
  { href: "/process", label: "Process View", icon: "◇" },
  { href: "/anomalies", label: "Anomalies", icon: "!" },
  { href: "/reports", label: "Reports", icon: "↓" },
];

export default function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="w-56 h-screen border-r border-slate-200 bg-white flex flex-col">
      {/* Brand */}
      <div className="px-5 py-5 border-b border-slate-100">
        <h1 className="text-[15px] font-semibold tracking-tight text-slate-900">
          FlowGuard AI
        </h1>
        <p className="text-[11px] text-slate-400 mt-0.5 tracking-wide uppercase">
          Process Intelligence
        </p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-2.5 px-3 py-2 rounded text-[13px] font-medium transition-colors ${
                active
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              }`}
            >
              <span className="text-[14px] w-4 text-center opacity-70">
                {item.icon}
              </span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="px-4 py-3 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <div className="min-w-0">
            <p className="text-[12px] font-medium text-slate-700 truncate">
              {user?.email}
            </p>
            <p className="text-[11px] text-slate-400">{user?.role}</p>
          </div>
          <button
            onClick={logout}
            className="text-[11px] text-slate-400 hover:text-slate-700 px-2 py-1"
          >
            Sign out
          </button>
        </div>
      </div>
    </aside>
  );
}
```

### `frontend/src/components/dashboard-shell.tsx`

```tsx
/**
 * Dashboard shell — wraps authenticated pages with sidebar.
 * Handles auth check and redirects to /login if not authenticated.
 */
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";
import Sidebar from "./sidebar";

function AuthGuard({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [user, loading, router]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-[13px] text-slate-400">Loading...</div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-slate-50/50">
        {children}
      </main>
    </div>
  );
}

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <AuthProvider>
      <AuthGuard>{children}</AuthGuard>
    </AuthProvider>
  );
}
```

### `frontend/src/lib/api.ts`

```ts
/**
 * API client — Axios instance with JWT auth interceptor.
 *
 * All API calls go through this. It automatically attaches the
 * Authorization header from localStorage and handles 401 redirects.
 */
import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const api = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle 401 — redirect to login
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
```

### `frontend/src/lib/auth.tsx`

```tsx
/**
 * Auth context — provides user state and auth methods to the app.
 *
 * Uses React Context + localStorage for token persistence.
 * Wraps the entire authenticated portion of the app.
 */
"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import api from "./api";

interface User {
  id: number;
  email: string;
  role: string;
  is_active: boolean;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // On mount, try to restore session from token
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      api
        .get("/users/me")
        .then((res) => setUser(res.data))
        .catch(() => localStorage.removeItem("token"))
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const res = await api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    localStorage.setItem("token", res.data.access_token);

    const me = await api.get("/users/me");
    setUser(me.data);
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem("token");
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
```

### `frontend/src/lib/types.ts`

```ts
/**
 * Shared TypeScript types matching backend API responses.
 */

// ── Auth ─────────────────────────────────────────────────────────────────────

export interface User {
  id: number;
  email: string;
  role: "Admin" | "Manager" | "Analyst";
  is_active: boolean;
}

// ── Upload ───────────────────────────────────────────────────────────────────

export interface UploadResponse {
  id: number;
  filename: string;
  original_name: string;
  status: "valid" | "invalid" | "error";
  total_traces: number | null;
  total_events: number | null;
  unique_activities: number | null;
  errors: string[];
  warnings: string[];
  raw_path: string;
  cleaned_path: string | null;
}

export interface UploadHistoryItem {
  id: number;
  original_name: string;
  status: string;
  uploaded_at: string;
  total_traces: number | null;
  total_events: number | null;
  unique_activities: number | null;
  raw_path: string;
  cleaned_path: string | null;
}

// ── Process Mining ───────────────────────────────────────────────────────────

export interface ProcessNode {
  id: string;
  label: string;
  count: number;
  is_start: boolean;
  is_end: boolean;
}

export interface ProcessEdge {
  source: string;
  target: string;
  count: number;
  avg_duration_seconds: number | null;
}

export interface ActivityStats {
  count: number;
  first_occurrence: string | null;
  last_occurrence: string | null;
  avg_duration_seconds: number | null;
  median_duration_seconds: number | null;
  resources: string[];
  departments: string[];
}

export interface ProcessGraphResponse {
  nodes: ProcessNode[];
  edges: ProcessEdge[];
  activity_stats: Record<string, ActivityStats>;
  metadata: {
    total_activities: number;
    total_transitions: number;
    total_events: number;
  };
}

// ── Anomaly Detection ────────────────────────────────────────────────────────

export interface AnomalyRun {
  id: number;
  upload_id: number;
  status: "pending" | "running" | "completed" | "failed";
  algorithm: string;
  contamination: number;
  n_anomalies: number | null;
  anomaly_rate: number | null;
  started_at: string | null;
  completed_at: string | null;
  error_message: string | null;
}

export interface AnomalyCaseResult {
  case_id: string;
  is_anomaly: boolean;
  anomaly_score: number;
  confidence: number;
  n_events: number;
  n_unique_activities: number;
}

export interface AnomalyResultsResponse {
  run: AnomalyRun;
  total_cases: number;
  total_anomalies: number;
  anomaly_rate: number;
  results: AnomalyCaseResult[];
}

// ── Explanations ─────────────────────────────────────────────────────────────

export interface ExplanationItem {
  rule: string;
  description: string;
  severity: "low" | "warning" | "high";
  details: Record<string, unknown>;
}

export interface CaseExplanation {
  case_id: string;
  is_anomaly: boolean;
  anomaly_score: number;
  severity_score: number;
  summary: string;
  explanations: ExplanationItem[];
}
```

---

## 5. Dependencies & UI Libraries

### From `package.json`

| Package | Version | Role |
|---------|---------|------|
| `next` | 16.3.0 | Framework (App Router) |
| `react` | 19.2.8 | UI library |
| `react-dom` | 19.2.8 | DOM renderer |
| `axios` | ^1.19.0 | HTTP client |
| `@xyflow/react` | ^12.11.3 | Interactive graph visualization (Process View) |
| `recharts` | ^3.10.1 | Charting library (Dashboard bar chart) |
| `tailwindcss` | ^4 | Utility-first CSS |
| `@tailwindcss/postcss` | ^4 | PostCSS plugin for Tailwind v4 |
| `typescript` | ^5 | Type checking |

**UI component libraries: NONE.** No shadcn/ui, no Radix, no Headless UI, no MUI, no Ant Design. Every UI element (buttons, tables, dropdowns, badges, modals) is hand-built with raw HTML + Tailwind utility classes.

**Icon libraries: NONE.** The sidebar uses plain Unicode characters (□, ↑, ◇, !, ↓) as icon stand-ins — no Lucide, no Heroicons, no icon font.

### PostCSS Configuration

Only plugin: `@tailwindcss/postcss`. No Autoprefixer, no cssnano, no other plugins listed.

---

## 6. Pages That Do NOT Exist Yet

Comparing against a standard enterprise process-mining platform spec:

| Page / Feature | Status |
|---|---|
| Login (`/login`) | **EXISTS** |
| Dashboard (`/dashboard`) | **EXISTS** |
| Upload Data (`/upload`) | **EXISTS** |
| Process View (`/process`) | **EXISTS** |
| Anomaly Center (`/anomalies`) | **EXISTS** |
| Reports (`/reports`) | **EXISTS** |
| Settings / User Profile page | **DOES NOT EXIST** |
| Admin / User Management page | **DOES NOT EXIST** |
| Model Training / Configuration page | **DOES NOT EXIST** |
| Notification / Alert Center | **DOES NOT EXIST** |
| Case Detail drill-down page (standalone) | **DOES NOT EXIST** — explanation detail is an inline side panel in the Anomalies page, not a separate route |
| 404 / Not Found page | **DOES NOT EXIST** — uses Next.js default |
| Error boundary page | **DOES NOT EXIST** |

All 6 core functional pages (Login, Dashboard, Upload, Process View, Anomalies, Reports) are fully built and wired. The missing pages are auxiliary/admin pages that were not part of the core build phases.

---

## 7. Component Inventory — Where Each Sub-Component Is Defined

All sub-components are defined **inline within the page file** that uses them. There are no shared component files for KPI cards, badges, tables, etc.

| Component | Defined In | Used In |
|---|---|---|
| `KpiCard` | `dashboard/page.tsx` (line 20) | Dashboard only |
| `ChartCard` | `dashboard/page.tsx` (line 294) | Dashboard only |
| `ChartPlaceholder` | `dashboard/page.tsx` (line 305) | Dashboard only |
| `InfoRow` | `dashboard/page.tsx` (line 313) | Dashboard only |
| `Th` | `dashboard/page.tsx` (line 322) | Dashboard only |
| `Td` | `dashboard/page.tsx` (line 330) | Dashboard only |
| `ScoreBadge` | `dashboard/page.tsx` (line 338) | Dashboard only |
| `EmptyState` | `dashboard/page.tsx` (line 348) | Dashboard only |
| `StatusBadge` | `upload/page.tsx` (line 239) | Upload only |
| `Metric` | `upload/page.tsx` (line 253) | Upload only |
| `ScorePill` | `anomalies/page.tsx` (line 275) | Anomalies only |
| `SeverityDot` | `anomalies/page.tsx` (line 290) | Anomalies only |
| `Stat` | `process/page.tsx` (line 275) | Process View only |
| `DashboardShell` | `components/dashboard-shell.tsx` | All authenticated pages |
| `Sidebar` | `components/sidebar.tsx` | Via DashboardShell |
| `AuthProvider` / `useAuth` | `lib/auth.tsx` | Login + DashboardShell |
| `api` (Axios instance) | `lib/api.ts` | All pages |

**Note:** `ScoreBadge` (dashboard) and `ScorePill` (anomalies) are functionally identical — same rendering logic, different names, defined separately in their respective files.

---

## End of Audit
