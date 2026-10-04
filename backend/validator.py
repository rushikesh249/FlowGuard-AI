"""
validator.py
────────────
XES event-log validation for FlowGuard AI (Module 2).

Schema grounded in: datasets/raw/BPI_Challenge_2019.xes
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

# ── Schema constants (from BPI_Challenge_2019.xes) ───────────────────────────

# Trace-level attributes that must be present on every case
REQUIRED_TRACE_ATTRIBUTES: list[str] = [
    "concept:name",
    "Purchasing Document",
    "Item",
    "Item Type",
    "GR-Based Inv. Verif.",
    "Goods Receipt",
    "Source",
    "Purch. Doc. Category name",
    "Company",
    "Spend classification text",
    "Spend area text",
    "Sub spend area text",
    "Vendor",
    "Name",
    "Document Type",
    "Item Category",
]

# Event-level columns that must exist in the flattened DataFrame
REQUIRED_EVENT_COLUMNS: list[str] = [
    "concept:name",         # activity name
    "time:timestamp",       # event timestamp
    "org:resource",         # resource / user performing the event
    "User",                 # SAP user field
    "Cumulative net worth (EUR)",
]

# Columns whose value must not be null or the sentinel "UNKNOWN"
MANDATORY_NON_NULL_EVENT_COLUMNS: list[str] = [
    "concept:name",
    "time:timestamp",
    "org:resource",
]

# Unique identifier columns for duplicate detection
DUPLICATE_KEY_COLUMNS: list[str] = [
    "case:concept:name",  # case ID column added by pm4py convert_to_dataframe
    "concept:name",
    "time:timestamp",
]


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    total_traces: int = 0
    total_events: int = 0
    unique_activities: int = 0
    cleaned_df: Optional[pd.DataFrame] = None


# ── Main validation function ──────────────────────────────────────────────────

def validate_xes(file_path: str) -> ValidationResult:
    """
    Parse and validate a .xes event log file.

    Parameters
    ----------
    file_path : str
        Absolute path to the uploaded .xes file.

    Returns
    -------
    ValidationResult
        Populated dataclass with validation outcome, counts, and cleaned data.
    """
    result = ValidationResult(is_valid=True)

    # ── Step 1: Parse the XES file with PM4Py ────────────────────────────────
    try:
        import pm4py  # lazy import — pm4py is large
        log = pm4py.read_xes(file_path)
    except Exception as exc:
        result.is_valid = False
        result.errors.append(f"Failed to parse XES file: {exc}")
        return result

    # ── Step 2: Convert to flat DataFrame (before counting) ──────────────────
    # pm4py may represent each event as its own single-event trace, so we
    # cannot rely on len(log) for the trace count.  Converting to a flat
    # DataFrame first and then computing counts from it is reliable.
    try:
        df = pm4py.convert_to_dataframe(log)
    except Exception as exc:
        result.is_valid = False
        result.errors.append(f"Failed to convert XES log to DataFrame: {exc}")
        return result

    # ── Step 3: Compute accurate counts from the DataFrame ────────────────────
    # Trace / case count: group by the case-ID column.
    # pm4py prefixes trace-level attributes with "case:" in the flat DF.
    # BPI 2019 uses "case:concept:name" as the case identifier.
    # Fallback: any "case:Name" column if the standard one is absent.
    case_id_col: Optional[str] = None
    for candidate in ("case:concept:name", "case:Name"):
        if candidate in df.columns:
            case_id_col = candidate
            break

    if case_id_col:
        result.total_traces = int(df[case_id_col].nunique())
    else:
        # Last resort: fall back to raw log length (may be inaccurate)
        result.total_traces = len(log)
        result.warnings.append(
            "Could not identify a case-ID column in the DataFrame; "
            "trace count may be inaccurate."
        )

    result.total_events = len(df)

    if result.total_traces == 0:
        result.is_valid = False
        result.errors.append("XES file contains zero traces.")
        return result

    if result.total_events == 0:
        result.is_valid = False
        result.errors.append("XES file contains zero events.")
        return result

    # Unique activity names (event types)
    if "concept:name" in df.columns:
        result.unique_activities = int(df["concept:name"].nunique())
    else:
        result.unique_activities = 0

    # ── Step 4: Check required event-level columns ────────────────────────────
    missing_event_cols = [c for c in REQUIRED_EVENT_COLUMNS if c not in df.columns]
    if missing_event_cols:
        result.is_valid = False
        for col in missing_event_cols:
            result.errors.append(f"Missing required event column: '{col}'")

    # ── Step 5: Check required trace-level attributes ─────────────────────────
    # pm4py prefixes trace attributes with "case:" in the flat DataFrame
    prefixed_trace_attrs = [f"case:{attr}" for attr in REQUIRED_TRACE_ATTRIBUTES]
    missing_trace_attrs = [a for a in prefixed_trace_attrs if a not in df.columns]
    if missing_trace_attrs:
        for attr in missing_trace_attrs:
            # Treat missing trace attributes as warnings (not all logs will have all fields)
            result.warnings.append(f"Missing trace attribute column: '{attr}'")

    # ── Step 6: Missing / null values in mandatory event columns ──────────────
    for col in MANDATORY_NON_NULL_EVENT_COLUMNS:
        if col not in df.columns:
            continue  # already flagged in step 4
        null_count = df[col].isna().sum()
        unknown_count = (df[col].astype(str).str.strip().str.upper() == "UNKNOWN").sum()
        if null_count > 0:
            result.warnings.append(
                f"Column '{col}' has {null_count} null value(s)."
            )
        if col in ("concept:name", "org:resource") and unknown_count > 0:
            result.warnings.append(
                f"Column '{col}' has {unknown_count} 'UNKNOWN' sentinel value(s)."
            )

    # ── Step 7: Duplicate event detection ────────────────────────────────────
    dup_key_cols_present = [c for c in DUPLICATE_KEY_COLUMNS if c in df.columns]
    if len(dup_key_cols_present) == len(DUPLICATE_KEY_COLUMNS):
        duplicate_mask = df.duplicated(subset=dup_key_cols_present, keep=False)
        dup_count = duplicate_mask.sum()
        if dup_count > 0:
            result.warnings.append(
                f"Found {dup_count} duplicate event row(s) "
                f"(same case, activity, and timestamp). "
                f"They will be removed in the cleaned version."
            )
    else:
        dup_count = 0

    # ── Step 8: Build cleaned DataFrame ──────────────────────────────────────
    cleaned = df.copy()

    # Drop exact duplicates on key columns
    if dup_count > 0 and len(dup_key_cols_present) == len(DUPLICATE_KEY_COLUMNS):
        cleaned = cleaned.drop_duplicates(subset=dup_key_cols_present, keep="first")

    result.cleaned_df = cleaned

    logger.info(
        "Validation complete | valid=%s | traces=%d | events=%d | "
        "activities=%d | errors=%d | warnings=%d",
        result.is_valid,
        result.total_traces,
        result.total_events,
        result.unique_activities,
        len(result.errors),
        len(result.warnings),
    )

    return result
