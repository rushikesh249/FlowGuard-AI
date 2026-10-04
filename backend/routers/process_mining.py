"""
routers/process_mining.py
──────────────────────────
Module 3 – Process Mining API endpoints.

Endpoints
---------
GET /process-mine/graph          Reconstruct the workflow graph from a cleaned upload.
GET /process-mine/case/{case_id} Activity sequence for a single case / trace.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_active_user
from models import UploadedFile, User
from schemas import CaseDetailResponse, ProcessGraphResponse
from process_mining import analyze_process, get_case_detail

logger = logging.getLogger(__name__)

router = APIRouter()


# ── GET /process-mine/graph ──────────────────────────────────────────────────

@router.get(
    "/graph",
    response_model=ProcessGraphResponse,
    summary="Reconstruct the workflow graph",
    description=(
        "Runs process mining on the cleaned event log from a previous upload. "
        "Returns a directly-follows graph (nodes + edges), per-activity "
        "statistics, and dataset metadata."
    ),
)
def get_process_graph(
    upload_id: int = Query(..., description="ID of the uploaded file to analyse"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> ProcessGraphResponse:
    record = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Upload not found.")
    if record.status != "valid":
        raise HTTPException(
            status_code=400,
            detail="Upload was not validated successfully.",
        )
    if not record.cleaned_path:
        raise HTTPException(
            status_code=400,
            detail="No cleaned CSV available for this upload.",
        )

    try:
        result = analyze_process(record.cleaned_path)
    except Exception as exc:
        logger.error("Process mining failed for upload %d: %s", upload_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Process mining failed: {exc}",
        ) from exc

    return ProcessGraphResponse(**result)


# ── GET /process-mine/case/{case_id} ─────────────────────────────────────────

@router.get(
    "/case/{case_id}",
    response_model=CaseDetailResponse,
    summary="Get activity sequence for a single case",
    description=(
        "Returns the full ordered list of activities, timestamps, durations, "
        "and metadata for one case / trace in the uploaded event log."
    ),
)
def get_case(
    case_id: str,
    upload_id: int = Query(..., description="ID of the uploaded file to query"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    record = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()

    if not record:
        raise HTTPException(status_code=404, detail="Upload not found.")
    if not record.cleaned_path:
        raise HTTPException(
            status_code=400,
            detail="No cleaned CSV available for this upload.",
        )

    try:
        detail = get_case_detail(record.cleaned_path, case_id)
    except Exception as exc:
        logger.error("Case lookup failed for %s: %s", case_id, exc)
        raise HTTPException(
            status_code=500,
            detail=f"Case lookup failed: {exc}",
        ) from exc

    if detail is None:
        raise HTTPException(status_code=404, detail=f"Case '{case_id}' not found.")

    return CaseDetailResponse(**detail)
