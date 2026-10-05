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
  p90_duration_seconds: number | null;
  resources: string[];
  resource_counts: Record<string, number>;
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
