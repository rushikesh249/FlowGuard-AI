"""
reports/generator.py
────────────────────
Computes data for all four report types from the cleaned event-log CSV
and (optionally) anomaly detection results.

Report types
────────────
• executive   — High-level KPIs, top anomalies, summary
• department  — Per-department breakdown
• anomaly     — Full anomaly list with explanations
• monthly     — Time-series: events and anomalies per month
"""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

import pandas as pd

from ai.anomaly_detection import load_results
from ai.explainers import explain_single_case

import hashlib
import json
import os

logger = logging.getLogger(__name__)


# ── Caching Helpers ──────────────────────────────────────────────────────────

def _get_cache_path(cleaned_csv: str, prefix: str, anomaly_results_path: Optional[str] = None, extra: str = "") -> str:
    key_str = f"{cleaned_csv}:{anomaly_results_path}:{extra}"
    h = hashlib.md5(key_str.encode()).hexdigest()[:12]
    return f"{cleaned_csv}.{prefix}_{h}.cache.json"

def _load_cached_json(cache_path: str, source_paths: list[Optional[str]]) -> Optional[dict]:
    if not os.path.exists(cache_path):
        return None
    try:
        cache_mtime = os.path.getmtime(cache_path)
        for p in source_paths:
            if p and os.path.exists(p) and os.path.getmtime(p) > cache_mtime:
                return None
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        logger.warning("Failed to load cache %s: %s", cache_path, exc)
        return None

def _save_cached_json(cache_path: str, data: dict) -> None:
    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception as exc:
        logger.warning("Failed to save cache %s: %s", cache_path, exc)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    if "time:timestamp" in df.columns:
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")
    return df


def _detect_case_col(df: pd.DataFrame) -> Optional[str]:
    for c in ("case:concept:name", "case:Name"):
        if c in df.columns:
            return c
    return None


def _detect_dept_col(df: pd.DataFrame) -> Optional[str]:
    for c in ("case:Sub spend area text", "case:Spend area text", "case:Company"):
        if c in df.columns:
            return c
    return None


def _detect_vendor_col(df: pd.DataFrame) -> Optional[str]:
    for c in ("case:Vendor", "case:Name", "Vendor", "vendor"):
        if c in df.columns:
            return c
    return None


# ── Executive Summary ────────────────────────────────────────────────────────

def generate_executive(
    cleaned_csv: str,
    anomaly_results_path: Optional[str] = None,
    upload_meta: Optional[dict] = None,
) -> dict[str, Any]:
    """
    High-level summary: total cases, events, anomaly rate, health score,
    top 10 most severe anomalies.
    """
    cache_path = _get_cache_path(cleaned_csv, "exec", anomaly_results_path)
    cached = _load_cached_json(cache_path, [cleaned_csv, anomaly_results_path])
    if cached:
        return cached

    df = _load_csv(cleaned_csv)
    case_col = _detect_case_col(df)
    n_events = len(df)
    n_cases = df[case_col].nunique() if case_col else 0
    n_activities = df["concept:name"].nunique() if "concept:name" in df.columns else 0

    # Date range
    if "time:timestamp" in df.columns:
        date_min = df["time:timestamp"].min()
        date_max = df["time:timestamp"].max()
        date_range = f"{date_min.strftime('%Y-%m-%d')} to {date_max.strftime('%Y-%m-%d')}" if pd.notna(date_min) else "N/A"
    else:
        date_range = "N/A"

    result: dict[str, Any] = {
        "title": "Executive Summary",
        "generated_at": datetime.utcnow().isoformat(),
        "date_range": date_range,
        "total_cases": n_cases,
        "total_events": n_events,
        "unique_activities": n_activities,
        "n_anomalies": 0,
        "anomaly_rate": 0.0,
        "health_score": 100,
        "top_anomalies": [],
    }

    if anomaly_results_path:
        anomalies = load_results(anomaly_results_path)
        flagged = [a for a in anomalies if a.get("is_anomaly")]
        n_anom = len(flagged)
        rate = n_anom / len(anomalies) if anomalies else 0

        result["n_anomalies"] = n_anom
        result["anomaly_rate"] = round(rate * 100, 2)
        result["health_score"] = round((1 - rate) * 100)
        result["total_cases"] = len(anomalies)

        # Top 10 by score
        flagged.sort(key=lambda x: -x.get("anomaly_score", 0))
        result["top_anomalies"] = flagged[:10]

    _save_cached_json(cache_path, result)
    return result


# ── Department Report ────────────────────────────────────────────────────────

def generate_department(
    cleaned_csv: str,
    anomaly_results_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Per-department breakdown: case count, event count, avg duration,
    anomaly rate.
    """
    cache_path = _get_cache_path(cleaned_csv, "dept", anomaly_results_path)
    cached = _load_cached_json(cache_path, [cleaned_csv, anomaly_results_path])
    if cached:
        return cached

    df = _load_csv(cleaned_csv)
    case_col = _detect_case_col(df)
    dept_col = _detect_dept_col(df)

    result: dict[str, Any] = {
        "title": "Department Report",
        "generated_at": datetime.utcnow().isoformat(),
        "departments": [],
    }

    if not dept_col or not case_col:
        return result

    # Build a case→department mapping (take first value per case, fill NaN with Unassigned)
    case_dept = (
        df.groupby(case_col)[dept_col]
        .first()
        .fillna("Unassigned")
        .reset_index()
        .rename(columns={dept_col: "department"})
    )

    # Merge back
    df = df.merge(case_dept, on=case_col, how="left", suffixes=("", "_dept"))
    df["department"] = df["department"].fillna("Unassigned")
    dept_key = "department"

    grouped = df.groupby(dept_key)
    departments: list[dict] = []

    for dept, group in grouped:
        n_events = len(group)
        n_cases = group[case_col].nunique()

        # Duration
        case_durations = group.groupby(case_col)["time:timestamp"].apply(
            lambda g: (g.max() - g.min()).total_seconds() if len(g) > 1 else 0
        )
        avg_duration_hrs = round(case_durations.mean() / 3600, 2) if len(case_durations) else 0

        # Unique resources
        n_resources = group["org:resource"].nunique() if "org:resource" in df.columns else 0

        entry: dict[str, Any] = {
            "department": str(dept),
            "n_cases": n_cases,
            "n_events": n_events,
            "n_resources": n_resources,
            "avg_duration_hours": avg_duration_hrs,
            "n_anomalies": 0,
            "anomaly_rate": 0.0,
        }
        departments.append(entry)

    # If anomaly results exist, compute per-department anomaly rate
    if anomaly_results_path:
        anomalies = load_results(anomaly_results_path)
        anomalous_ids = {a["case_id"] for a in anomalies if a.get("is_anomaly")}
        case_ids_by_dept = df.groupby(dept_key)[case_col].apply(set).to_dict()

        for dept_entry in departments:
            dept = dept_entry["department"]
            dept_cases = case_ids_by_dept.get(dept, set())
            n_anom = len(dept_cases & anomalous_ids)
            dept_entry["n_anomalies"] = n_anom
            dept_entry["anomaly_rate"] = round(n_anom / len(dept_cases) * 100, 2) if dept_cases else 0

    departments.sort(key=lambda d: -d["n_cases"])
    result["departments"] = departments
    _save_cached_json(cache_path, result)
    return result


# ── Anomaly Report ───────────────────────────────────────────────────────────

def generate_anomaly(
    cleaned_csv: str,
    anomaly_results_path: str,
    include_explanations: bool = True,
    explanation_cap: int = 100,
) -> dict[str, Any]:
    """
    Full anomaly list with optional explanations.

    Precomputes dataset statistics and extracts case events in a single
    pass over the DataFrame to eliminate redundant file I/O.
    """
    anomalies = load_results(anomaly_results_path)
    flagged = [a for a in anomalies if a.get("is_anomaly")]

    result: dict[str, Any] = {
        "title": "Anomaly Report",
        "generated_at": datetime.utcnow().isoformat(),
        "total_cases": len(anomalies),
        "total_anomalies": len(flagged),
        "anomaly_rate": round(len(flagged) / len(anomalies) * 100, 2) if anomalies else 0,
        "anomalies": [],
    }

    # Sort by score descending so the most severe cases get explanations first
    flagged.sort(key=lambda x: -x.get("anomaly_score", 0))

    target_cases = flagged[:explanation_cap] if include_explanations else []
    target_ids = {str(a["case_id"]) for a in target_cases}

    # Precompute dataset stats and case events map once
    dataset_stats: dict[str, Any] = {}
    case_events_map: dict[str, list[dict]] = {}

    if include_explanations and target_cases:
        from ai.explainers import compute_dataset_stats, _build_case_events_map
        dataset_stats = compute_dataset_stats(cleaned_csv)
        df = _load_csv(cleaned_csv)
        case_events_map = _build_case_events_map(df, target_case_ids=target_ids)

    for i, a in enumerate(flagged):
        case_id = str(a["case_id"])
        entry: dict[str, Any] = {
            "case_id": case_id,
            "anomaly_score": a["anomaly_score"],
            "confidence": a["confidence"],
            "n_events": a["n_events"],
            "n_unique_activities": a["n_unique_activities"],
            "explanations": [],
            "summary": "",
            "severity_score": 0,
        }

        if include_explanations and i < explanation_cap:
            try:
                events = case_events_map.get(case_id, [])
                expl = explain_single_case(
                    cleaned_csv,
                    case_id,
                    a,
                    dataset_stats=dataset_stats,
                    case_events=events,
                )
                entry["explanations"] = expl.get("explanations", [])
                entry["summary"] = expl.get("summary", "")
                entry["severity_score"] = expl.get("severity_score", 0)
            except Exception as exc:
                logger.warning("Explanation failed for %s: %s", case_id, exc)

        result["anomalies"].append(entry)

    return result


# ── Monthly Report ───────────────────────────────────────────────────────────

def generate_monthly(
    cleaned_csv: str,
    anomaly_results_path: Optional[str] = None,
) -> dict[str, Any]:
    """
    Time-series: events per month, anomalies per month.
    """
    cache_path = _get_cache_path(cleaned_csv, "month", anomaly_results_path)
    cached = _load_cached_json(cache_path, [cleaned_csv, anomaly_results_path])
    if cached:
        return cached

    df = _load_csv(cleaned_csv)
    case_col = _detect_case_col(df)

    result: dict[str, Any] = {
        "title": "Monthly Report",
        "generated_at": datetime.utcnow().isoformat(),
        "months": [],
    }

    if "time:timestamp" not in df.columns:
        return result

    df["_month"] = df["time:timestamp"].dt.to_period("M").astype(str)

    # Events per month
    events_per_month = df.groupby("_month").size().to_dict()

    # Cases per month (first event month for each case)
    cases_per_month: dict[str, int] = {}
    if case_col:
        first_event = df.groupby(case_col)["_month"].first()
        cases_per_month = first_event.value_counts().to_dict()

    # Anomalies per month (if available)
    anomaly_per_month: dict[str, int] = {}
    if anomaly_results_path:
        anomalies = load_results(anomaly_results_path)
        anomalous_ids = {a["case_id"] for a in anomalies if a.get("is_anomaly")}
        if case_col:
            anom_cases = df[df[case_col].isin(anomalous_ids)]
            first_anom = anom_cases.groupby(case_col)["_month"].first()
            anomaly_per_month = first_anom.value_counts().to_dict()

    # Build timeline
    all_months = sorted(set(events_per_month.keys()) | set(cases_per_month.keys()))
    months: list[dict] = []
    for m in all_months:
        months.append({
            "month": m,
            "n_events": events_per_month.get(m, 0),
            "n_cases": cases_per_month.get(m, 0),
            "n_anomalies": anomaly_per_month.get(m, 0),
        })

    result["months"] = months
    _save_cached_json(cache_path, result)
    return result


# ── Vendor Breakdown ─────────────────────────────────────────────────────────

def generate_vendors(
    cleaned_csv: str,
    anomaly_results_path: Optional[str] = None,
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Top vendors breakdown by case count, event count, spend, and anomaly rate.
    """
    cache_path = _get_cache_path(cleaned_csv, "vend", anomaly_results_path, extra=str(top_n))
    cached = _load_cached_json(cache_path, [cleaned_csv, anomaly_results_path])
    if cached:
        return cached

    df = _load_csv(cleaned_csv)
    case_col = _detect_case_col(df)
    vendor_col = _detect_vendor_col(df)

    result: dict[str, Any] = {
        "title": "Vendor Breakdown",
        "generated_at": datetime.utcnow().isoformat(),
        "vendors": [],
    }

    if not vendor_col or not case_col:
        return result

    spend_col = "Cumulative net worth (EUR)" if "Cumulative net worth (EUR)" in df.columns else None

    # Aggregate by case
    agg_dict = {vendor_col: "first"}
    if spend_col:
        agg_dict[spend_col] = "max"

    case_summary = df.groupby(case_col).agg(agg_dict).reset_index()

    anomalous_ids: set[str] = set()
    if anomaly_results_path:
        anomalies = load_results(anomaly_results_path)
        anomalous_ids = {str(a["case_id"]) for a in anomalies if a.get("is_anomaly")}

    vendors_list: list[dict] = []
    for vendor_name, group in case_summary.groupby(vendor_col):
        if pd.isna(vendor_name) or not str(vendor_name).strip():
            continue
        case_ids = set(group[case_col].astype(str))
        n_cases = len(case_ids)
        n_anom = len(case_ids & anomalous_ids) if anomalous_ids else 0
        total_spend = float(group[spend_col].sum()) if spend_col else 0.0

        vendors_list.append({
            "vendor": str(vendor_name),
            "n_cases": n_cases,
            "total_spend_eur": round(total_spend, 2),
            "n_anomalies": n_anom,
            "anomaly_rate": round(n_anom / n_cases * 100, 2) if n_cases else 0.0,
        })

    vendors_list.sort(key=lambda x: -x["n_cases"])
    result["vendors"] = vendors_list[:top_n]
    _save_cached_json(cache_path, result)
    return result


# ── CSV export helpers ───────────────────────────────────────────────────────

def executive_to_rows(data: dict) -> list[dict]:
    """Flatten executive summary to CSV rows."""
    return [
        {"metric": "Total Cases", "value": data["total_cases"]},
        {"metric": "Total Events", "value": data["total_events"]},
        {"metric": "Unique Activities", "value": data["unique_activities"]},
        {"metric": "Anomalies Detected", "value": data["n_anomalies"]},
        {"metric": "Anomaly Rate (%)", "value": data["anomaly_rate"]},
        {"metric": "Health Score", "value": data["health_score"]},
        {"metric": "Date Range", "value": data["date_range"]},
        {"metric": "Generated At", "value": data["generated_at"]},
    ]


def department_to_rows(data: dict) -> list[dict]:
    return data.get("departments", [])


def anomaly_to_rows(data: dict) -> list[dict]:
    rows = []
    for a in data.get("anomalies", []):
        row = {
            "case_id": a["case_id"],
            "anomaly_score": a["anomaly_score"],
            "confidence": a["confidence"],
            "n_events": a["n_events"],
            "severity_score": a.get("severity_score", 0),
            "summary": a.get("summary", ""),
            "explanations": "; ".join(
                e.get("description", "") for e in a.get("explanations", [])
            ),
        }
        rows.append(row)
    return rows


def monthly_to_rows(data: dict) -> list[dict]:
    return data.get("months", [])
