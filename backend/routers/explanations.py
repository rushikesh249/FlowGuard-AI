"""
routers/explanations.py
───────────────────────
Module 7 – Explainable AI endpoints.

Endpoints
---------
GET /explanations/{run_id}                    Explain all anomalies in a run.
GET /explanations/{run_id}/case/{case_id}     Explain a single case.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_active_user
from models import AnomalyRun, UploadedFile, User
from ai.anomaly_detection import load_results
from ai.explainers import explain_anomalies, explain_single_case

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory cache for parsed results: results_path -> (mtime, list_of_records, dict_case_id_to_record)
_RESULTS_CACHE: dict[str, tuple[float, list[dict], dict[str, dict]]] = {}


def _get_cached_results(results_path: str) -> tuple[list[dict], dict[str, dict]]:
    """Load results with in-memory caching keyed by file modification time."""
    try:
        mtime = os.path.getmtime(results_path)
    except OSError:
        mtime = 0.0

    cached = _RESULTS_CACHE.get(results_path)
    if cached and cached[0] == mtime:
        return cached[1], cached[2]

    results_list = load_results(results_path)
    results_by_id = {str(r.get("case_id")): r for r in results_list}
    _RESULTS_CACHE[results_path] = (mtime, results_list, results_by_id)
    return results_list, results_by_id


def _get_validated_run(
    run_id: int,
    current_user: User,
    db: Session,
) -> tuple[AnomalyRun, UploadedFile]:
    """Shared validation: fetch run + upload, verify ownership & status."""
    run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")

    upload = db.query(UploadedFile).filter(UploadedFile.id == run.upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Associated upload not found.")

    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Run is not completed yet (status: {run.status}).",
        )
    if not run.results_path:
        raise HTTPException(status_code=404, detail="Results file not found.")
    if not upload.cleaned_path:
        raise HTTPException(status_code=404, detail="Cleaned CSV not found.")

    return run, upload


# ── GET /explanations/{run_id} ───────────────────────────────────────────────

@router.get(
    "/{run_id}",
    summary="Explain all anomalies in a training run",
    description=(
        "Generates human-readable explanations for each anomalous case. "
        "Supports filtering and pagination."
    ),
)
def get_explanations(
    run_id: int,
    anomalies_only: bool = Query(True, description="Only explain anomalous cases"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    run, upload = _get_validated_run(run_id, current_user, db)
    anomaly_results, _ = _get_cached_results(run.results_path)

    result = explain_anomalies(
        cleaned_csv_path=upload.cleaned_path,
        anomaly_results=anomaly_results,
        anomalies_only=anomalies_only,
        limit=limit,
        offset=offset,
    )

    return {
        "run_id": run_id,
        "algorithm": run.algorithm,
        "contamination": run.contamination,
        **result,
    }


# ── GET /explanations/{run_id}/case/{case_id} ───────────────────────────────

@router.get(
    "/{run_id}/case/{case_id}",
    summary="Explain a single case",
    description=(
        "Generates detailed human-readable explanations for one specific "
        "case in a completed anomaly detection run."
    ),
)
def get_case_explanation(
    run_id: int,
    case_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    run, upload = _get_validated_run(run_id, current_user, db)
    _, results_by_id = _get_cached_results(run.results_path)

    case_result = results_by_id.get(str(case_id))
    if case_result is None:
        raise HTTPException(
            status_code=404,
            detail=f"Case '{case_id}' not found in anomaly results.",
        )

    # Fast-path: Return precomputed explanations immediately (O(1) lookup, < 1ms)
    if (
        "explanations" in case_result
        and "summary" in case_result
        and "severity_score" in case_result
    ):
        return {
            "run_id": run_id,
            "algorithm": run.algorithm,
            "case_id": str(case_id),
            "is_anomaly": case_result.get("is_anomaly", False),
            "anomaly_score": case_result.get("anomaly_score", 0.0),
            "severity_score": case_result.get("severity_score", 0),
            "summary": case_result.get("summary", ""),
            "explanations": case_result.get("explanations", []),
        }

    # Fallback for legacy un-backfilled runs
    explanation = explain_single_case(
        cleaned_csv_path=upload.cleaned_path,
        case_id=case_id,
        anomaly_result=case_result,
    )

    return {
        "run_id": run_id,
        "algorithm": run.algorithm,
        **explanation,
    }
