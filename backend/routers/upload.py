"""
routers/upload.py
─────────────────
Module 2 – Data Upload & Validation endpoints.

Endpoints
---------
POST /upload/xes         Authenticated. Upload a .xes event-log file.
GET  /upload/history     Authenticated. List all uploads by the current user.
"""
from __future__ import annotations

import os
import uuid
import logging
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_active_user, require_roles
from models import UploadedFile, User, Role
from schemas import UploadHistoryItem, UploadResponse
from validator import validate_xes

logger = logging.getLogger(__name__)

router = APIRouter()

# ── Storage directories ───────────────────────────────────────────────────────
# These paths are relative to the working directory inside the container.
# docker-compose mounts ../datasets → /app/datasets
RAW_DIR     = os.path.join("datasets", "raw")
CLEANED_DIR = os.path.join("datasets", "cleaned")

def _ensure_dirs() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    os.makedirs(CLEANED_DIR, exist_ok=True)


# ── POST /upload/xes ──────────────────────────────────────────────────────────

@router.post(
    "/xes",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an XES event-log file",
    description=(
        "Upload a .xes process event-log file. "
        "The file is validated against the BPI Challenge 2019 schema "
        "(required event/trace attributes, missing values, duplicates). "
        "Both the raw file and a cleaned CSV are stored on disk. "
        "Returns full validation results immediately."
    ),
)
async def upload_xes(
    file: Annotated[UploadFile, File(description="XES event-log file (.xes)")],
    current_user: User = Depends(require_roles(Role.Admin, Role.Manager)),
    db: Session = Depends(get_db),
) -> UploadResponse:
    _ensure_dirs()

    # ── 1. Extension check ────────────────────────────────────────────────────
    original_name = file.filename or "upload.xes"
    if not original_name.lower().endswith(".xes"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{os.path.splitext(original_name)[1]}'. "
                   "Only .xes files are accepted.",
        )

    # ── 2. Save raw file ──────────────────────────────────────────────────────
    uid = uuid.uuid4().hex
    stored_filename = f"{uid}_{original_name}"
    raw_path = os.path.join(RAW_DIR, stored_filename)

    try:
        content = await file.read()
        with open(raw_path, "wb") as f:
            f.write(content)
    except Exception as exc:
        logger.error("Failed to save uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save uploaded file to disk.",
        ) from exc
    finally:
        await file.close()

    # ── 3. Create a pending DB record ─────────────────────────────────────────
    db_record = UploadedFile(
        filename=stored_filename,
        original_name=original_name,
        status="pending",
        uploaded_by=current_user.id,
        uploaded_at=datetime.now(timezone.utc),
        raw_path=raw_path,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    # ── 4. Run validation ─────────────────────────────────────────────────────
    try:
        result = validate_xes(raw_path)
    except Exception as exc:
        logger.error("Unhandled error in validate_xes: %s", exc)
        db_record.status = "invalid"
        db_record.validation_errors = [f"Internal validation error: {exc}"]
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation error: {exc}",
        ) from exc

    # ── 5. Save cleaned CSV (if valid) ────────────────────────────────────────
    cleaned_path: str | None = None
    if result.is_valid and result.cleaned_df is not None:
        cleaned_filename = f"{uid}_cleaned.csv"
        cleaned_path = os.path.join(CLEANED_DIR, cleaned_filename)
        try:
            result.cleaned_df.to_csv(cleaned_path, index=False)
        except Exception as exc:
            logger.warning("Could not save cleaned CSV: %s", exc)
            cleaned_path = None

    # ── 6. Update DB record ───────────────────────────────────────────────────
    db_record.total_traces = result.total_traces
    db_record.total_events = result.total_events
    db_record.unique_activities = result.unique_activities

    if result.is_valid and cleaned_path is None:
        # Validation passed but we couldn't save the cleaned CSV — mark as error
        db_record.status = "error"
        db_record.validation_errors = ["Validation passed but failed to save cleaned CSV to disk."]
    else:
        db_record.status = "valid" if result.is_valid else "invalid"
        db_record.validation_errors = result.errors if result.errors else None
    db_record.cleaned_path = cleaned_path
    db.commit()
    db.refresh(db_record)

    # ── 7. Return response ────────────────────────────────────────────────────
    return UploadResponse(
        id=db_record.id,
        filename=db_record.filename,
        original_name=db_record.original_name,
        status=db_record.status,
        total_traces=result.total_traces,
        total_events=result.total_events,
        unique_activities=result.unique_activities,
        errors=result.errors,
        warnings=result.warnings,
        raw_path=db_record.raw_path,
        cleaned_path=cleaned_path,
    )


# ── GET /upload/history ───────────────────────────────────────────────────────

@router.get(
    "/history",
    response_model=list[UploadHistoryItem],
    summary="List all uploads for the organization",
)
def get_upload_history(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100, description="Max results to return"),
    offset: int = Query(default=0, ge=0, description="Number of results to skip"),
) -> list[UploadHistoryItem]:
    records = (
        db.query(UploadedFile)
        .order_by(UploadedFile.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return records
