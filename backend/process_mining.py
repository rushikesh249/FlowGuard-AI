"""
process_mining.py
─────────────────
Module 3 – Process Mining Engine (PRD Module 3/4).

Takes a cleaned event-log CSV and reconstructs the Procure-to-Pay workflow
as a directly-follows graph with per-activity metadata.

Uses pure pandas for graph construction (robust across PM4Py versions)
and PM4Py only for XES/CSV parsing when needed.
"""
from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _detect_case_id_col(df: pd.DataFrame) -> Optional[str]:
    """Return the case-ID column name present in *df*, or None."""
    for candidate in ("case:concept:name", "case:Name"):
        if candidate in df.columns:
            return candidate
    return None


def _ensure_datetime(df: pd.DataFrame, col: str = "time:timestamp") -> pd.Series:
    """Coerce *col* to datetime if it isn't already."""
    if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
        return pd.to_datetime(df[col], utc=True, errors="coerce")
    return df[col]


# ── DFG discovery (pure pandas) ──────────────────────────────────────────────

def _discover_dfg_from_df(df: pd.DataFrame) -> dict:
    """
    Build a directly-follows graph from a flat event-log DataFrame.

    Returns
    -------
    dict with keys:
        start_activities  : dict[str, int]
        end_activities    : dict[str, int]
        transitions       : dict[(str, str), int]
        transition_durations : dict[(str, str), list[float]]  — seconds
    """
    case_col = _detect_case_id_col(df)
    if case_col is None:
        raise ValueError(
            "Cannot identify case-ID column. "
            "Expected 'case:concept:name' or 'case:Name'."
        )

    work = df[[case_col, "concept:name", "time:timestamp"]].copy()
    work["time:timestamp"] = _ensure_datetime(work)
    work = work.sort_values([case_col, "time:timestamp"]).reset_index(drop=True)

    # Vectorised: shift activity & case within the sorted frame
    work["_prev_act"]  = work["concept:name"].shift(1)
    work["_prev_case"] = work[case_col].shift(1)
    work["_prev_ts"]   = work["time:timestamp"].shift(1)

    # Mark boundaries (first event of each case)
    is_boundary = work["_prev_case"] != work[case_col]

    # Start / end activities
    first_mask = is_boundary
    last_mask  = work[case_col] != work[case_col].shift(-1)

    start_activities: dict[str, int] = (
        work.loc[first_mask, "concept:name"]
        .value_counts()
        .to_dict()
    )
    end_activities: dict[str, int] = (
        work.loc[last_mask, "concept:name"]
        .value_counts()
        .to_dict()
    )

    # Transitions (exclude cross-case boundaries)
    trans_df = work[~is_boundary].copy()
    transitions: dict[tuple[str, str], int] = defaultdict(int)
    transition_durations: dict[tuple[str, str], list[float]] = defaultdict(list)

    for src, tgt, dur in zip(
        trans_df["_prev_act"],
        trans_df["concept:name"],
        (trans_df["time:timestamp"] - trans_df["_prev_ts"]).dt.total_seconds(),
    ):
        key = (src, tgt)
        transitions[key] += 1
        if pd.notna(dur) and dur >= 0:
            transition_durations[key].append(float(dur))

    return {
        "start_activities": start_activities,
        "end_activities": end_activities,
        "transitions": dict(transitions),
        "transition_durations": dict(transition_durations),
    }


# ── Activity statistics ──────────────────────────────────────────────────────

def _compute_activity_stats(df: pd.DataFrame) -> dict[str, dict]:
    """Per-activity descriptive statistics."""
    df = df.copy()
    df["time:timestamp"] = _ensure_datetime(df)

    stats: dict[str, dict] = {}
    grouped = df.groupby("concept:name")

    for activity, group in grouped:
        timestamps = group["time:timestamp"].dropna()
        # Flat unique list (preserved for backward compat — used by process/page.tsx)
        resources  = group["org:resource"].dropna().unique().tolist() if "org:resource" in df.columns else []
        # Count dict (top-50 by frequency — used by dashboard Widget 4 approver bars)
        if "org:resource" in df.columns:
            rc_series = group["org:resource"].dropna().value_counts().head(50)
            resource_counts: dict = {str(k): int(v) for k, v in rc_series.items()}
        else:
            resource_counts = {}

        entry: dict = {
            "count": int(len(group)),
            "first_occurrence": timestamps.min().isoformat() if len(timestamps) else None,
            "last_occurrence":  timestamps.max().isoformat() if len(timestamps) else None,
            "resources":        resources[:50],  # flat list — cap payload size
            "resource_counts":  resource_counts,  # {id: count} dict for distribution charts
        }

        # Department (trace-level attribute, prefixed "case:")
        for dept_col in ("case:Sub spend area text", "case:Spend area text"):
            if dept_col in df.columns:
                entry["departments"] = group[dept_col].dropna().unique().tolist()[:20]
                break

        stats[activity] = entry

    # Inter-event durations within each case (vectorised)
    case_col = _detect_case_id_col(df)
    if case_col:
        work = df[[case_col, "concept:name", "time:timestamp"]].copy()
        work = work.sort_values([case_col, "time:timestamp"])
        work["_prev_ts"]   = work.groupby(case_col)["time:timestamp"].shift(1)
        work["_duration"]  = (work["time:timestamp"] - work["_prev_ts"]).dt.total_seconds()

        durations = (
            work.dropna(subset=["_duration"])
            .groupby("concept:name")["_duration"]
        )
        for activity, group in durations:
            vals = group[group >= 0]
            if activity in stats and len(vals):
                stats[activity]["avg_duration_seconds"] = round(float(vals.mean()), 2)
                stats[activity]["median_duration_seconds"] = round(float(vals.median()), 2)
                stats[activity]["p90_duration_seconds"] = round(float(vals.quantile(0.9)), 2)

    return stats


# ── Case detail ──────────────────────────────────────────────────────────────

def get_case_detail(cleaned_csv_path: str, case_id: str) -> Optional[dict]:
    """
    Return the ordered activity sequence for a single case / trace.

    Returns None if *case_id* is not found in the dataset.
    """
    df = pd.read_csv(cleaned_csv_path, low_memory=False)
    case_col = _detect_case_id_col(df)
    if case_col is None:
        return None

    case_df = df[df[case_col] == case_id].copy()
    if case_df.empty:
        return None

    case_df["time:timestamp"] = _ensure_datetime(case_df)
    case_df = case_df.sort_values("time:timestamp").reset_index(drop=True)

    # Durations
    case_df["_duration"] = case_df["time:timestamp"].diff().dt.total_seconds().fillna(0)
    case_df["_prev_ts"]  = case_df["time:timestamp"].shift(1)

    activities: list[dict] = []
    for _, row in case_df.iterrows():
        entry: dict = {
            "activity":    row.get("concept:name"),
            "timestamp":   row["time:timestamp"].isoformat() if pd.notna(row["time:timestamp"]) else None,
            "resource":    row.get("org:resource"),
            "duration_seconds": float(row["_duration"]) if pd.notna(row["_duration"]) else 0,
        }
        # Attach useful trace-level attributes if present
        for attr in ("case:Vendor", "case:Document Type", "case:Company"):
            if attr in row.index:
                key = attr.replace("case:", "").replace(" ", "_")
                entry[key] = row[attr]
        activities.append(entry)

    return {"case_id": case_id, "activities": activities}


# ── Public entry point ───────────────────────────────────────────────────────

def analyze_process(cleaned_csv_path: str) -> dict:
    """
    Full process-mining analysis on a cleaned event-log CSV.

    Returns
    -------
    dict
        {
            "nodes": [ {"id", "label", "count", "is_start", "is_end"} ],
            "edges": [ {"source", "target", "count", "avg_duration_seconds"} ],
            "activity_stats": { activity_name: {...} },
            "metadata": { "total_activities", "total_transitions", "total_events" }
        }
    """
    # ── Check disk cache ──────────────────────────────────────────────────
    import json
    import os
    cache_path = f"{cleaned_csv_path}.graph_cache.json"
    if os.path.exists(cache_path):
        try:
            if os.path.getmtime(cache_path) >= os.path.getmtime(cleaned_csv_path):
                logger.info("Serving process graph from cache: %s", cache_path)
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as exc:
            logger.warning("Failed to read graph cache %s: %s", cache_path, exc)

    logger.info("Loading cleaned CSV: %s", cleaned_csv_path)
    df = pd.read_csv(cleaned_csv_path, low_memory=False)
    logger.info("Loaded %d rows, %d columns", len(df), len(df.columns))

    # 1. Discover DFG
    dfg = _discover_dfg_from_df(df)

    start_acts = set(dfg["start_activities"].keys())
    end_acts   = set(dfg["end_activities"].keys())
    all_activities = (
        start_acts
        | end_acts
        | {a for (a, _) in dfg["transitions"]}
        | {b for (_, b) in dfg["transitions"]}
    )

    # 1.5. Raw activity counts from the log (total occurrences per activity)
    activity_counts: dict[str, int] = df["concept:name"].value_counts().to_dict()

    # 2. Build node list
    nodes = [
        {
            "id": act,
            "label": act,
            "count": int(activity_counts.get(act, 0)),
            "is_start": act in start_acts,
            "is_end":   act in end_acts,
        }
        for act in sorted(all_activities)
    ]

    # 3. Build edge list
    edges = []
    for (src, tgt), count in sorted(dfg["transitions"].items(), key=lambda x: -x[1]):
        durations = dfg["transition_durations"].get((src, tgt), [])
        edges.append({
            "source": src,
            "target": tgt,
            "count": count,
            "avg_duration_seconds": (
                round(sum(durations) / len(durations), 2) if durations else None
            ),
        })

    # 4. Per-activity statistics
    activity_stats = _compute_activity_stats(df)

    # 5. Metadata
    metadata = {
        "total_activities": len(all_activities),
        "total_transitions": len(dfg["transitions"]),
        "total_events": len(df),
    }

    logger.info(
        "Analysis complete | activities=%d | transitions=%d | events=%d",
        metadata["total_activities"],
        metadata["total_transitions"],
        metadata["total_events"],
    )

    result = {
        "nodes": nodes,
        "edges": edges,
        "activity_stats": activity_stats,
        "metadata": metadata,
    }

    try:
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(result, f)
        logger.info("Saved process graph to cache: %s", cache_path)
    except Exception as exc:
        logger.warning("Failed to write graph cache %s: %s", cache_path, exc)

    return result
