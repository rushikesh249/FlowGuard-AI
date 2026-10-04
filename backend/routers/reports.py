"""
routers/reports.py
──────────────────
Module 9 – Report generation endpoints.

Endpoints
---------
GET /reports/executive/{upload_id}    Executive summary report (CSV).
GET /reports/department/{upload_id}   Department breakdown report (CSV).
GET /reports/anomaly/{run_id}         Detailed anomaly report (CSV).
GET /reports/monthly/{upload_id}      Monthly time-series report (CSV).

All endpoints return downloadable CSV reports.
"""
from __future__ import annotations

import csv
import io
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_current_active_user
from models import AnomalyRun, UploadedFile, User

from reports.generator import (
    generate_executive,
    generate_department,
    generate_anomaly,
    generate_monthly,
    generate_vendors,
    executive_to_rows,
    department_to_rows,
    anomaly_to_rows,
    monthly_to_rows,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_upload(upload_id: int, user: User, db: Session) -> UploadedFile:
    upload = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Upload not found.")
    if upload.cleaned_path is None:
        raise HTTPException(status_code=400, detail="No cleaned CSV available.")
    return upload


def _get_run(run_id: int, user: User, db: Session) -> tuple[AnomalyRun, UploadedFile]:
    run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    upload = db.query(UploadedFile).filter(UploadedFile.id == run.upload_id).first()
    if not upload:
        raise HTTPException(status_code=404, detail="Associated upload not found.")
    if str(run.status) != "completed":
        raise HTTPException(status_code=400, detail="Run not completed.")
    if run.results_path is None:
        raise HTTPException(status_code=404, detail="Results not found.")
    if upload.cleaned_path is None:
        raise HTTPException(status_code=404, detail="Cleaned CSV not found.")
    return run, upload


def _csv_response(rows: list[dict], filename: str) -> Response:
    if not rows:
        return Response(content="No data", media_type="text/plain")

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── GET /reports/executive/{upload_id} ───────────────────────────────────────

@router.get("/executive/{upload_id}", summary="Executive Summary report (CSV)")
def report_executive(
    upload_id: int,
    format: str = Query("csv", description="Export format (csv)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    upload = _get_upload(upload_id, current_user, db)

    # Find latest completed run for this upload
    run = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id, AnomalyRun.status == "completed")
        .order_by(AnomalyRun.id.desc())
        .first()
    )
    results_path = str(run.results_path) if (run is not None and run.results_path is not None) else None

    data = generate_executive(
        str(upload.cleaned_path),
        anomaly_results_path=results_path,
        upload_meta={"filename": str(upload.original_name)},
    )

    return _csv_response(executive_to_rows(data), "executive_summary.csv")


# ── GET /reports/department/{upload_id} ──────────────────────────────────────

@router.get("/department/{upload_id}", summary="Department report (CSV)")
def report_department(
    upload_id: int,
    format: str = Query("csv", description="Export format (csv)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    upload = _get_upload(upload_id, current_user, db)

    run = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id, AnomalyRun.status == "completed")
        .order_by(AnomalyRun.id.desc())
        .first()
    )
    results_path = str(run.results_path) if (run is not None and run.results_path is not None) else None

    data = generate_department(str(upload.cleaned_path), anomaly_results_path=results_path)

    return _csv_response(department_to_rows(data), "department_report.csv")


# ── GET /reports/anomaly/{run_id} ────────────────────────────────────────────

@router.get("/anomaly/{run_id}", summary="Anomaly report (CSV)")
def report_anomaly(
    run_id: int,
    format: str = Query("csv", description="Export format (csv)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    run, upload = _get_run(run_id, current_user, db)

    data = generate_anomaly(
        str(upload.cleaned_path),
        str(run.results_path),
        include_explanations=True,
    )

    return _csv_response(anomaly_to_rows(data), "anomaly_report.csv")


# ── GET /reports/monthly/{upload_id} ─────────────────────────────────────────

@router.get("/monthly/{upload_id}", summary="Monthly report (CSV)")
def report_monthly(
    upload_id: int,
    format: str = Query("csv", description="Export format (csv)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Response:
    upload = _get_upload(upload_id, current_user, db)

    run = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id, AnomalyRun.status == "completed")
        .order_by(AnomalyRun.id.desc())
        .first()
    )
    results_path = str(run.results_path) if (run is not None and run.results_path is not None) else None

    data = generate_monthly(str(upload.cleaned_path), anomaly_results_path=results_path)

    return _csv_response(monthly_to_rows(data), "monthly_report.csv")


# ── JSON Data Endpoints for Dashboard Widgets ────────────────────────────────

@router.get("/data/department/{upload_id}", summary="Department breakdown JSON data")
def data_department(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    upload = _get_upload(upload_id, current_user, db)
    run = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id, AnomalyRun.status == "completed")
        .order_by(AnomalyRun.id.desc())
        .first()
    )
    results_path = str(run.results_path) if (run is not None and run.results_path is not None) else None
    return generate_department(str(upload.cleaned_path), anomaly_results_path=results_path)


@router.get("/data/monthly/{upload_id}", summary="Monthly time-series JSON data")
def data_monthly(
    upload_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    upload = _get_upload(upload_id, current_user, db)
    run = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id, AnomalyRun.status == "completed")
        .order_by(AnomalyRun.id.desc())
        .first()
    )
    results_path = str(run.results_path) if (run is not None and run.results_path is not None) else None
    return generate_monthly(str(upload.cleaned_path), anomaly_results_path=results_path)


@router.get("/data/vendors/{upload_id}", summary="Top vendors breakdown JSON data")
def data_vendors(
    upload_id: int,
    top_n: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> dict:
    upload = _get_upload(upload_id, current_user, db)
    run = (
        db.query(AnomalyRun)
        .filter(AnomalyRun.upload_id == upload_id, AnomalyRun.status == "completed")
        .order_by(AnomalyRun.id.desc())
        .first()
    )
    results_path = str(run.results_path) if (run is not None and run.results_path is not None) else None
    return generate_vendors(str(upload.cleaned_path), anomaly_results_path=results_path, top_n=top_n)
