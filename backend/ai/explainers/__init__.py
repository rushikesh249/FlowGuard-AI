"""
ai/explainers/__init__.py
──────────────────────────
Composite Explainer — orchestrates all individual explainers and
produces a unified explanation for each anomalous case.

This is the single public entry point for the Explainable AI module.
The API router calls ``explain_anomalies()`` and nothing else.

Design
──────
• New explainers are added to ``DEFAULT_EXPLAINERS`` — no other code
  changes required (open/closed principle).
• Dataset stats are computed once and shared across all explainers.
• Output is a list of ``CaseExplanation`` objects, serialisable to JSON.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

import pandas as pd

from .base import BaseExplainer, CaseExplanation, Explanation
from .rules import (
    DuplicateActivityExplainer,
    OutOfOrderSequenceExplainer,
    PaymentWithoutPOExplainer,
    SkippedApprovalExplainer,
    UnusualCaseLengthExplainer,
)
from .statistics import (
    DurationAnomalyExplainer,
    EventCountAnomalyExplainer,
    ResourceAnomalyExplainer,
    compute_dataset_stats,
)

logger = logging.getLogger(__name__)

# ── Default explainer registry ────────────────────────────────────────────────
# Order matters: rules first (deterministic), then statistical.

DEFAULT_EXPLAINERS: list[BaseExplainer] = [
    SkippedApprovalExplainer(),
    PaymentWithoutPOExplainer(),
    OutOfOrderSequenceExplainer(),
    DuplicateActivityExplainer(),
    UnusualCaseLengthExplainer(),
    DurationAnomalyExplainer(),
    ResourceAnomalyExplainer(),
    EventCountAnomalyExplainer(),
]

# Severity weights for computing the case-level severity score
_SEVERITY_WEIGHTS = {"low": 1, "warning": 3, "high": 5}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_case_events_from_df(case_df: pd.DataFrame) -> list[dict]:
    """Extract ordered events for a single case DataFrame."""
    if case_df.empty:
        return []

    if "time:timestamp" in case_df.columns:
        if not pd.api.types.is_datetime64_any_dtype(case_df["time:timestamp"]):
            case_df = case_df.copy()
            case_df["time:timestamp"] = pd.to_datetime(
                case_df["time:timestamp"], utc=True, errors="coerce"
            )
        case_df = case_df.sort_values("time:timestamp")

    events: list[dict] = []
    prev_ts = None
    for row in case_df.to_dict("records"):
        ts = row.get("time:timestamp")
        duration = 0.0
        if prev_ts is not None and pd.notna(ts):
            duration = (ts - prev_ts).total_seconds()
        if pd.notna(ts):
            prev_ts = ts

        events.append({
            "activity":         row.get("concept:name"),
            "timestamp":        ts.isoformat() if pd.notna(ts) and hasattr(ts, "isoformat") else (str(ts) if pd.notna(ts) else None),
            "resource":         row.get("org:resource"),
            "duration_seconds": max(duration, 0),
        })

    return events


def _build_case_events_map(df: pd.DataFrame, target_case_ids: Optional[set[str]] = None) -> dict[str, list[dict]]:
    """Build a mapping of case_id -> list of event dicts in one pass."""
    case_col = None
    for candidate in ("case:concept:name", "case:Name"):
        if candidate in df.columns:
            case_col = candidate
            break
    if case_col is None:
        return {}

    if target_case_ids is not None:
        df = df[df[case_col].astype(str).isin(target_case_ids)].copy()

    if df.empty:
        return {}

    if "time:timestamp" in df.columns:
        if not pd.api.types.is_datetime64_any_dtype(df["time:timestamp"]):
            df["time:timestamp"] = pd.to_datetime(
                df["time:timestamp"], utc=True, errors="coerce"
            )
        df = df.sort_values([case_col, "time:timestamp"])

    case_events_map: dict[str, list[dict]] = {}
    for case_id, group in df.groupby(case_col):
        case_events_map[str(case_id)] = _extract_case_events_from_df(group)

    return case_events_map


def _load_case_events(cleaned_csv_path: str, case_id: str) -> list[dict]:
    """Load ordered events for a single case from the cleaned CSV."""
    import pandas as pd
    df = pd.read_csv(cleaned_csv_path, low_memory=False)
    events_map = _build_case_events_map(df, target_case_ids={str(case_id)})
    return events_map.get(str(case_id), [])


def _generate_summary(explanations: list[Explanation]) -> str:
    """Create a one-line summary from the list of explanations."""
    if not explanations:
        return "No specific rule violations detected. Flagged by statistical model."

    high = [e for e in explanations if e.severity == "high"]
    if high:
        return f"{len(high)} critical issue(s): " + "; ".join(
            e.description for e in high[:2]
        )
    return f"{len(explanations)} issue(s) detected: " + "; ".join(
        e.description for e in explanations[:2]
    )


def _compute_severity_score(explanations: list[Explanation]) -> int:
    """Compute a 0–10 severity score from the explanations."""
    if not explanations:
        return 0
    raw = sum(_SEVERITY_WEIGHTS.get(e.severity, 1) for e in explanations)
    # Cap at 10
    return min(raw, 10)


def _explanation_to_dict(exp: Explanation) -> dict:
    return {
        "rule": exp.rule,
        "description": exp.description,
        "severity": exp.severity,
        "details": exp.details,
    }


def _case_explanation_to_dict(ce: CaseExplanation) -> dict:
    return {
        "case_id": ce.case_id,
        "is_anomaly": ce.is_anomaly,
        "anomaly_score": ce.anomaly_score,
        "severity_score": ce.severity_score,
        "summary": ce.summary,
        "explanations": [_explanation_to_dict(e) for e in ce.explanations],
    }


# ── Public API ────────────────────────────────────────────────────────────────

def explain_anomalies(
    cleaned_csv_path: str,
    anomaly_results: list[dict],
    anomalies_only: bool = True,
    explainers: Optional[list[BaseExplainer]] = None,
    limit: int = 100,
    offset: int = 0,
) -> dict:
    """
    Generate human-readable explanations for anomaly results.

    Parameters
    ----------
    cleaned_csv_path : str
        Path to the cleaned CSV (from Phase 2).
    anomaly_results : list[dict]
        Per-case anomaly results (from Phase 4 — the JSON on disk).
    anomalies_only : bool
        If True, only explain cases flagged as anomalous.
    explainers : list[BaseExplainer] | None
        Override the default explainer set.
    limit / offset : int
        Pagination over the results.

    Returns
    -------
    dict with keys:
        explained_cases : list[dict]  — serialised CaseExplanation objects
        total_explained  : int
        dataset_stats    : dict       — computed dataset statistics
    """
    import pandas as pd

    if explainers is None:
        explainers = DEFAULT_EXPLAINERS

    # Filter to anomalies if requested
    cases = anomaly_results
    if anomalies_only:
        cases = [c for c in cases if c.get("is_anomaly")]

    total = len(cases)
    page = cases[offset : offset + limit]

    # Fast-path: if page records already have precomputed explanations, return immediately
    if page and all("explanations" in c and "summary" in c and "severity_score" in c for c in page):
        explained = [
            {
                "case_id": str(c["case_id"]),
                "is_anomaly": c.get("is_anomaly", False),
                "anomaly_score": c.get("anomaly_score", 0.0),
                "severity_score": c.get("severity_score", 0),
                "summary": c.get("summary", ""),
                "explanations": c.get("explanations", []),
            }
            for c in page
        ]
        return {
            "explained_cases": explained,
            "total_explained": total,
            "dataset_stats": {},
        }

    # Compute dataset statistics once
    logger.info("Computing dataset statistics from %s", cleaned_csv_path)
    dataset_stats = compute_dataset_stats(cleaned_csv_path)

    # Load cleaned CSV once for all cases in the page
    target_ids = {str(c["case_id"]) for c in page}
    df = pd.read_csv(cleaned_csv_path, low_memory=False)
    case_events_map = _build_case_events_map(df, target_case_ids=target_ids)

    # Generate explanations for each case in the page
    explained: list[dict] = []
    for case_result in page:
        case_id = str(case_result["case_id"])
        case_events = case_events_map.get(case_id, [])

        all_explanations: list[Explanation] = []
        for explainer in explainers:
            try:
                exps = explainer.explain(case_events, case_id, dataset_stats)
                all_explanations.extend(exps)
            except Exception as exc:
                logger.warning(
                    "Explainer %s failed for case %s: %s",
                    explainer.name, case_id, exc,
                )

        case_explanation = CaseExplanation(
            case_id=case_id,
            is_anomaly=case_result.get("is_anomaly", False),
            anomaly_score=case_result.get("anomaly_score", 0.0),
            explanations=all_explanations,
            summary=_generate_summary(all_explanations),
            severity_score=_compute_severity_score(all_explanations),
        )
        explained.append(_case_explanation_to_dict(case_explanation))

    logger.info(
        "Explained %d cases (%d total in page)", len(explained), total,
    )

    return {
        "explained_cases": explained,
        "total_explained": total,
        "dataset_stats": {
            "avg_events_per_case": dataset_stats.get("avg_events_per_case"),
            "median_events_per_case": dataset_stats.get("median_events_per_case"),
            "avg_duration_per_case_hours": (
                round(dataset_stats.get("avg_duration_per_case", 0) / 3600, 2)
                if dataset_stats.get("avg_duration_per_case") else None
            ),
        },
    }


def explain_single_case(
    cleaned_csv_path: str,
    case_id: str,
    anomaly_result: dict,
    explainers: Optional[list[BaseExplainer]] = None,
    dataset_stats: Optional[dict] = None,
    case_events: Optional[list[dict]] = None,
) -> dict:
    """
    Generate explanations for a single case.

    Accepts precomputed dataset_stats and case_events to avoid redundant I/O.
    If anomaly_result already contains precomputed explanation fields,
    returns them immediately without disk I/O.
    """
    if (
        "explanations" in anomaly_result
        and "summary" in anomaly_result
        and "severity_score" in anomaly_result
    ):
        return {
            "case_id": str(case_id),
            "is_anomaly": anomaly_result.get("is_anomaly", False),
            "anomaly_score": anomaly_result.get("anomaly_score", 0.0),
            "severity_score": anomaly_result.get("severity_score", 0),
            "summary": anomaly_result.get("summary", ""),
            "explanations": anomaly_result.get("explanations", []),
        }

    if explainers is None:
        explainers = DEFAULT_EXPLAINERS

    if dataset_stats is None:
        dataset_stats = compute_dataset_stats(cleaned_csv_path)

    if case_events is None:
        case_events = _load_case_events(cleaned_csv_path, case_id)

    all_explanations: list[Explanation] = []
    for explainer in explainers:
        try:
            exps = explainer.explain(case_events, case_id, dataset_stats)
            all_explanations.extend(exps)
        except Exception as exc:
            logger.warning(
                "Explainer %s failed for case %s: %s",
                explainer.name, case_id, exc,
            )

    case_explanation = CaseExplanation(
        case_id=str(case_id),
        is_anomaly=anomaly_result.get("is_anomaly", False),
        anomaly_score=anomaly_result.get("anomaly_score", 0.0),
        explanations=all_explanations,
        summary=_generate_summary(all_explanations),
        severity_score=_compute_severity_score(all_explanations),
    )
    return _case_explanation_to_dict(case_explanation)


def attach_explanations_to_results(
    results: list[dict],
    cleaned_csv_path: str,
    explainers: Optional[list[BaseExplainer]] = None,
) -> list[dict]:
    """
    Generate explanations, severity scores, and summaries for all cases at training time,
    attaching them directly to the results list before saving to disk.

    - Anomalous cases receive full rule-based and statistical explanations.
    - Normal cases receive default clean indicators (severity_score=0, clean summary, explanations=[]).

    Parameters
    ----------
    results : list[dict]
        Per-case anomaly results from format_results().
    cleaned_csv_path : str
        Path to the cleaned dataset CSV.
    explainers : list[BaseExplainer] | None
        Optional override for default explainers.

    Returns
    -------
    list[dict]
        Updated results list with 'severity_score', 'summary', and 'explanations' attached.
    """
    import pandas as pd

    if explainers is None:
        explainers = DEFAULT_EXPLAINERS

    logger.info("Computing dataset statistics from %s for explanation attachment", cleaned_csv_path)
    dataset_stats = compute_dataset_stats(cleaned_csv_path)

    # Collect anomalous case IDs
    anomalous_ids = {str(r["case_id"]) for r in results if r.get("is_anomaly")}
    logger.info(
        "Attaching explanations: %d anomalous cases out of %d total cases",
        len(anomalous_ids),
        len(results),
    )

    case_events_map: dict[str, list[dict]] = {}
    if anomalous_ids:
        logger.info("Loading cleaned dataset from %s to extract anomalous case events", cleaned_csv_path)
        df = pd.read_csv(cleaned_csv_path, low_memory=False)
        case_events_map = _build_case_events_map(df, target_case_ids=anomalous_ids)

    # Attach explanations to each result
    for r in results:
        case_id = str(r.get("case_id"))
        is_anomaly = bool(r.get("is_anomaly", False))

        if not is_anomaly:
            r["severity_score"] = 0
            r["summary"] = "Normal workflow execution. No anomalies detected."
            r["explanations"] = []
            continue

        case_events = case_events_map.get(case_id, [])
        all_explanations: list[Explanation] = []
        for explainer in explainers:
            try:
                exps = explainer.explain(case_events, case_id, dataset_stats)
                all_explanations.extend(exps)
            except Exception as exc:
                logger.warning(
                    "Explainer %s failed for case %s: %s",
                    explainer.name, case_id, exc,
                )

        r["severity_score"] = _compute_severity_score(all_explanations)
        r["summary"] = _generate_summary(all_explanations)
        r["explanations"] = [_explanation_to_dict(e) for e in all_explanations]

    logger.info("Successfully attached explanations to all %d cases", len(results))
    return results
