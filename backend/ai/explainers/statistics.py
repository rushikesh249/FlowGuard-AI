"""
ai/explainers/statistics.py
────────────────────────────
Statistical explainers that compare a case's metrics against
dataset-wide norms computed from the cleaned event log.

Explainers
──────────
1. DurationAnomaly    — case duration far from department / global average
2. ResourceAnomaly    — unusual resource count or unknown resource
3. EventCountAnomaly  — event count deviates significantly from norm
"""
from __future__ import annotations

from typing import Any

from .base import BaseExplainer, Explanation


# ── Dataset statistics computation ───────────────────────────────────────────

def compute_dataset_stats(cleaned_csv_path: str) -> dict[str, Any]:
    """
    Load the cleaned CSV and compute dataset-wide statistics used by
    all statistical explainers.

    This is called once per analysis run and cached/passed to explainers.

    Returns
    -------
    dict with keys:
        avg_events_per_case, std_events_per_case, median_events_per_case,
        avg_duration_per_case, std_duration_per_case, median_duration_per_case,
        avg_resources_per_case, activity_frequency (dict),
        dept_avg_duration (dict)
    """
    import pandas as pd

    df = pd.read_csv(cleaned_csv_path, low_memory=False)

    # Detect case ID column
    case_col = None
    for candidate in ("case:concept:name", "case:Name"):
        if candidate in df.columns:
            case_col = candidate
            break
    if case_col is None:
        return {}

    # Ensure datetime
    if "time:timestamp" in df.columns:
        df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True, errors="coerce")

    # Per-case aggregates
    grouped = df.groupby(case_col)
    events_per_case = grouped.size()
    durations_per_case = grouped["time:timestamp"].apply(
        lambda g: (g.max() - g.min()).total_seconds() if len(g) > 1 else 0
    )
    resources_per_case = grouped["org:resource"].nunique() if "org:resource" in df.columns else pd.Series(dtype=float)

    # Activity frequency (global)
    activity_freq: dict[str, int] = {}
    if "concept:name" in df.columns:
        activity_freq = df["concept:name"].value_counts().to_dict()

    # Department-level average duration
    dept_avg_duration: dict[str, float] = {}
    dept_col = None
    for col in ("case:Sub spend area text", "case:Spend area text"):
        if col in df.columns:
            dept_col = col
            break
    if dept_col and "time:timestamp" in df.columns:
        dept_durations = df.groupby([case_col, dept_col])["time:timestamp"].apply(
            lambda g: (g.max() - g.min()).total_seconds() if len(g) > 1 else 0
        ).reset_index()
        dept_avg_duration = dept_durations.groupby(dept_col)["time:timestamp"].mean().to_dict()

    return {
        "avg_events_per_case":    float(events_per_case.mean()),
        "std_events_per_case":    float(events_per_case.std()),
        "median_events_per_case": float(events_per_case.median()),
        "avg_duration_per_case":  float(durations_per_case.mean()),
        "std_duration_per_case":  float(durations_per_case.std()),
        "median_duration_per_case": float(durations_per_case.median()),
        "avg_resources_per_case": float(resources_per_case.mean()) if len(resources_per_case) else 0,
        "activity_frequency":     activity_freq,
        "dept_avg_duration":      dept_avg_duration,
    }


# ── Explainer 1: Duration Anomaly ────────────────────────────────────────────

class DurationAnomalyExplainer(BaseExplainer):
    """Compare case total duration against dataset / department average."""

    def explain(self, case_events, case_id, dataset_stats):
        if len(case_events) < 2:
            return []

        # Compute case duration from events
        from datetime import datetime as dt

        timestamps = []
        for e in case_events:
            ts = e.get("timestamp")
            if ts:
                try:
                    timestamps.append(dt.fromisoformat(ts))
                except (ValueError, TypeError):
                    pass

        if len(timestamps) < 2:
            return []

        case_duration = (max(timestamps) - min(timestamps)).total_seconds()
        avg = dataset_stats.get("avg_duration_per_case")
        std = dataset_stats.get("std_duration_per_case")

        if avg is None or std is None or std == 0:
            return []

        ratio = case_duration / avg if avg > 0 else 0
        z_score = (case_duration - avg) / std

        explanations: list[Explanation] = []

        if ratio > 5:
            explanations.append(Explanation(
                rule="extreme_duration",
                description=(
                    f"This case took {ratio:.0f}x longer than the dataset "
                    f"average ({case_duration / 3600:.1f}h vs "
                    f"{avg / 3600:.1f}h average)."
                ),
                severity="high",
                details={
                    "case_duration_hours": round(case_duration / 3600, 2),
                    "avg_duration_hours": round(avg / 3600, 2),
                    "ratio": round(ratio, 1),
                    "z_score": round(z_score, 2),
                },
            ))
        elif z_score > 2:
            explanations.append(Explanation(
                rule="long_duration",
                description=(
                    f"This case duration ({case_duration / 3600:.1f}h) is "
                    f"{z_score:.1f} standard deviations above the mean."
                ),
                severity="warning",
                details={
                    "case_duration_hours": round(case_duration / 3600, 2),
                    "z_score": round(z_score, 2),
                },
            ))

        return explanations


# ── Explainer 2: Resource Anomaly ────────────────────────────────────────────

class ResourceAnomalyExplainer(BaseExplainer):
    """Flag cases with unusual resource usage patterns."""

    def explain(self, case_events, case_id, dataset_stats):
        resources = {e.get("resource") for e in case_events if e.get("resource")}
        n_resources = len(resources)
        avg = dataset_stats.get("avg_resources_per_case", 0)

        explanations: list[Explanation] = []

        # Too many resources (potential unauthorised access)
        if avg > 0 and n_resources > avg * 3:
            explanations.append(Explanation(
                rule="excessive_resources",
                description=(
                    f"This case involved {n_resources} unique resources/users, "
                    f"which is {n_resources / avg:.1f}x the average ({avg:.1f}). "
                    "This may indicate unauthorised involvement."
                ),
                severity="warning",
                details={"n_resources": n_resources, "avg_resources": round(avg, 1)},
            ))

        # Unknown / batch resources
        unknown_count = sum(
            1 for r in resources
            if r and ("batch" in r.lower() or "unknown" in r.lower() or "system" in r.lower())
        )
        if unknown_count > 0 and n_resources > 1:
            explanations.append(Explanation(
                rule="automated_or_unknown_resource",
                description=(
                    f"{unknown_count} of {n_resources} resources in this case "
                    "appear to be automated/batch accounts. Verify if this "
                    "is expected."
                ),
                severity="low",
                details={"unknown_count": unknown_count, "total_resources": n_resources},
            ))

        return explanations


# ── Explainer 3: Event Count Anomaly ─────────────────────────────────────────

class EventCountAnomalyExplainer(BaseExplainer):
    """
    Flag cases where the event count significantly deviates from norm.
    This complements UnusualCaseLengthExplainer with z-score precision.
    """

    def explain(self, case_events, case_id, dataset_stats):
        n_events = len(case_events)
        avg = dataset_stats.get("avg_events_per_case")
        std = dataset_stats.get("std_events_per_case")

        if avg is None or std is None or std == 0:
            return []

        z_score = (n_events - avg) / std

        if abs(z_score) > 2.5:
            direction = "more" if z_score > 0 else "fewer"
            return [Explanation(
                rule="event_count_deviation",
                description=(
                    f"This case has {n_events} events — significantly "
                    f"{direction} than the dataset average "
                    f"({avg:.0f} ± {std:.0f}). "
                    f"Z-score: {z_score:.1f}."
                ),
                severity="warning",
                details={
                    "n_events": n_events,
                    "z_score": round(z_score, 2),
                    "avg": round(avg, 1),
                },
            )]
        return []
