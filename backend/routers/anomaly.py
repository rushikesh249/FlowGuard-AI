"""
routers/anomaly.py
──────────────────
Module 5/6 – Anomaly Detection API endpoints.

Endpoints
---------
POST /anomaly/train              Trigger model training (background Celery task).
GET  /anomaly/status/{run_id}    Check training run status.
GET  /anomaly/results/{run_id}   Fetch per-case anomaly results (paginated).
GET  /anomaly/runs               List all anomaly runs for an upload.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_active_user, require_roles
from models import AnomalyRun, UploadedFile, User, Role
from schemas import (
    AnomalyCaseResult,
    AnomalyResultsResponse,
    AnomalyRunResponse,
    TrainAnomalyRequest,
)
from ai.tasks import train_anomaly_model
from ai.anomaly_detection import load_results

logger = logging.getLogger(__name__)

router = APIRouter()


# ── POST /anomaly/train ─────────────────────────────────────────────────────

@router.post(
    "/train",
    response_model=AnomalyRunResponse,
    status_code=202,
    summary="Trigger anomaly detection training",
    description=(
        "Creates a new training run and dispatches it to the Celery worker. "
        "Returns immediately with the run ID; poll /anomaly/status/{run_id} "
        "for progress."
    ),
)
def trigger_training(
    body: TrainAnomalyRequest,
    current_user: User = Depends(require_roles(Role.Admin, Role.Manager)),
    db: Session = Depends(get_db),
) -> AnomalyRunResponse:
    # Validate upload exists
    upload = db.query(UploadedFile).filter(UploadedFile.id == body.upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found.")
    if upload.status != "valid":
        raise HTTPException(status_code=400, detail="Upload was not validated.")
    if not upload.cleaned_path:
        raise HTTPException(status_code=400, detail="No cleaned CSV available.")

    # Validate parameters
    if body.algorithm not in ("isolation_forest", "lof"):
        raise HTTPException(
            status_code=400,
            detail="Algorithm must be 'isolation_forest' or 'lof'.",
        )
    if not (0.001 <= body.contamination <= 0.5):
        raise HTTPException(
            status_code=400,
            detail="Contamination must be between 0.001 and 0.5.",
        )

    # Create run record
    run = AnomalyRun(
        upload_id=body.upload_id,
        algorithm=body.algorithm,
        contamination=body.contamination,
        status="pending",
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    # Dispatch to Celery worker
    train_anomaly_model.delay(
        run_id=run.id,
        upload_id=upload.id,
        algorithm=body.algorithm,
        contamination=body.contamination,
    )
    logger.info("Dispatched training task for run %d", run.id)

    return run


# ── GET /anomaly/status/{run_id} ─────────────────────────────────────────────

@router.get(
    "/status/{run_id}",
    response_model=AnomalyRunResponse,
    summary="Check training run status",
)
def get_run_status(
    run_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AnomalyRunResponse:
    run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    return run


# ── GET /anomaly/results/{run_id} ────────────────────────────────────────────

@router.get(
    "/results/{run_id}",
    response_model=AnomalyResultsResponse,
    summary="Fetch per-case anomaly results",
    description=(
        "Returns the anomaly results for a completed training run. "
        "Supports filtering (anomalies_only) and pagination (limit/offset)."
    ),
)
def get_results(
    run_id: int,
    anomalies_only: bool = Query(False, description="Return only anomalous cases"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> AnomalyResultsResponse:
    run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    if run.status != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Run is not completed yet (current status: {run.status}).",
        )

    if not run.results_path:
        raise HTTPException(status_code=404, detail="Results file not found.")

    # Load results from disk
    all_results = load_results(run.results_path)

    # Filter
    if anomalies_only:
        all_results = [r for r in all_results if r.get("is_anomaly")]

    total = len(all_results)
    page = all_results[offset : offset + limit]

    return AnomalyResultsResponse(
        run=AnomalyRunResponse.model_validate(run),
        total_cases=total,
        total_anomalies=run.n_anomalies or 0,
        anomaly_rate=run.anomaly_rate or 0.0,
        results=[AnomalyCaseResult(**r) for r in page],
    )


# ── GET /anomaly/runs ────────────────────────────────────────────────────────

@router.get(
    "/runs",
    response_model=list[AnomalyRunResponse],
    summary="List all anomaly runs for an upload",
)
def list_runs(
    upload_id: int = Query(..., description="Upload ID to list runs for"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> list[AnomalyRunResponse]:
    upload = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found.")

    runs = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id)
        .order_by(AnomalyRun.id.desc())
        .all()
    )
    return runs
