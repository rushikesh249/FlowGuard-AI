"""
ai/features.py
──────────────
Module 4/5 – Feature Engineering for Anomaly Detection.

Extracts a numerical feature vector per case (trace) from the cleaned
event-log CSV produced by Phase 2.  These features feed the Isolation
Forest (or other unsupervised model) in Phase 4.

Feature categories
──────────────────
• Volume        – event count, unique-activity count, resource diversity
• Duration      – total span, avg / median / max inter-event gap
• Repetition    – repeated-activity flag and count
• Sequence      – start / end activity encoding
"""
from __future__ import annotations

import logging
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


# ── Main entry point ─────────────────────────────────────────────────────────

def extract_features(cleaned_csv_path: str) -> pd.DataFrame:
    """
    Load a cleaned event-log CSV and return one feature row per case.

    Returns
    -------
    pd.DataFrame
        Index = case_id, columns = numerical features ready for sklearn.
    """
    logger.info("Loading cleaned CSV for feature extraction: %s", cleaned_csv_path)
    df = pd.read_csv(cleaned_csv_path, low_memory=False)

    case_col = _detect_case_id_col(df)
    if case_col is None:
        raise ValueError(
            "Cannot identify case-ID column. "
            "Expected 'case:concept:name' or 'case:Name'."
        )

    # Prepare working columns
    df["time:timestamp"] = _ensure_datetime(df)
    df = df.sort_values([case_col, "time:timestamp"])

    # ── Vectorised inter-event gap (within each case) ────────────────────────
    df["_prev_ts"] = df.groupby(case_col)["time:timestamp"].shift(1)
    df["_gap"] = (df["time:timestamp"] - df["_prev_ts"]).dt.total_seconds()

    # ── Build feature records ────────────────────────────────────────────────
    records: list[dict] = []
    grouped = df.groupby(case_col)

    for case_id, group in grouped:
        n_events = len(group)
        gaps = group["_gap"].dropna()
        gaps = gaps[gaps >= 0]  # filter negative gaps (data issues)

        feats: dict = {
            "case_id": case_id,

            # Volume features
            "n_events":              n_events,
            "n_unique_activities":   group["concept:name"].nunique(),
            "n_unique_resources":    group["org:resource"].nunique() if "org:resource" in df.columns else 0,

            # Duration features
            "total_duration_seconds":          (group["time:timestamp"].max() - group["time:timestamp"].min()).total_seconds() if n_events > 1 else 0.0,
            "avg_duration_between_events":     float(gaps.mean())  if len(gaps) else 0.0,
            "median_duration_between_events":  float(gaps.median()) if len(gaps) else 0.0,
            "max_duration_between_events":     float(gaps.max())   if len(gaps) else 0.0,

            # Repetition features
            "has_repeated_activity":  1 if group["concept:name"].duplicated().any() else 0,
            "n_repeated_activities":  int((group["concept:name"].value_counts() > 1).sum()),

            # Sequence features (categorical — encoded as strings, will be
            # label-encoded below)
            "start_activity": group["concept:name"].iloc[0],
            "end_activity":   group["concept:name"].iloc[-1],
        }
        records.append(feats)

    features_df = pd.DataFrame(records).set_index("case_id")

    # ── Label-encode categorical sequence features ───────────────────────────
    for col in ("start_activity", "end_activity"):
        features_df[col] = features_df[col].astype("category").cat.codes

    # ── Fill any remaining NaN with 0 ────────────────────────────────────────
    features_df = features_df.fillna(0)

    logger.info(
        "Feature extraction complete | %d cases × %d features",
        len(features_df), len(features_df.columns),
    )
    return features_df
