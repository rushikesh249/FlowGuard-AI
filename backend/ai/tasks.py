"""
ai/tasks.py
───────────
Celery background task for anomaly-detection model training.

Triggered by the API (POST /anomaly/train), runs asynchronously in the
Celery worker process.  Steps:

1. Mark the AnomalyRun as "running"
2. Load the cleaned CSV from Phase 2
3. Extract per-case features
4. Train Isolation Forest (or LOF)
5. Save model + results to disk
6. Update the AnomalyRun record with final status
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from celery_app import celery_app
from database import SessionLocal
from models import AnomalyRun, UploadedFile

logger = logging.getLogger(__name__)

# Directories for persisted artefacts (inside the container)
MODEL_DIR = os.path.join("ai", "models")
RESULTS_DIR = os.path.join("ai", "results")


@celery_app.task(bind=True, name="ai.tasks.train_anomaly_model")
def train_anomaly_model(
    self,
    run_id: int,
    upload_id: int,
    algorithm: str = "isolation_forest",
    contamination: float = 0.05,
) -> dict:
    """
    Full training pipeline — runs in the Celery worker.

    Returns a summary dict (also stored in the DB).
    """
    db = SessionLocal()
    try:
        run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
        upload = db.query(UploadedFile).filter(UploadedFile.id == upload_id).first()

        if not run or not upload:
            logger.error("Run %d or Upload %d not found", run_id, upload_id)
            return {"error": "Record not found"}

        # ── 1. Mark as running ──────────────────────────────────────────────
        run.status = "running"
        run.started_at = datetime.now(timezone.utc)
        db.commit()

        if not upload.cleaned_path or not os.path.exists(upload.cleaned_path):
            raise FileNotFoundError(
                f"Cleaned CSV not found: {upload.cleaned_path}"
            )

        # ── 2. Feature engineering ──────────────────────────────────────────
        from ai.features import extract_features
        from ai.anomaly_detection import (
            train_model,
            format_results,
            save_model,
            save_results,
        )

        logger.info("Extracting features from %s", upload.cleaned_path)
        features_df = extract_features(upload.cleaned_path)
        logger.info("Features: %d cases × %d dims", *features_df.shape)

        # ── 3. Train model ──────────────────────────────────────────────────
        logger.info("Training %s (contamination=%.3f)", algorithm, contamination)
        training_output = train_model(
            features_df,
            contamination=contamination,
            algorithm=algorithm,
        )

        # ── 4. Format results ───────────────────────────────────────────────
        results = format_results(
            features_df,
            training_output["predictions"],
            training_output["anomaly_scores"],
        )

        # ── 5. Generate and attach explanations ─────────────────────────────
        from ai.explainers import attach_explanations_to_results

        logger.info("Generating and attaching explanations for run %d", run_id)
        results = attach_explanations_to_results(results, upload.cleaned_path)

        # ── 6. Persist artefacts ────────────────────────────────────────────
        run_tag = f"run{run_id}_upload{upload_id}"

        paths = save_model(
            training_output["model"],
            training_output["scaler"],
            MODEL_DIR,
            run_tag,
        )
        results_path = save_results(results, RESULTS_DIR, run_tag)

        # ── 7. Update DB ────────────────────────────────────────────────────
        run.status = "completed"
        run.n_anomalies = training_output["n_anomalies"]
        run.anomaly_rate = training_output["anomaly_rate"]
        run.model_path = paths["model_path"]
        run.results_path = results_path
        run.completed_at = datetime.now(timezone.utc)
        db.commit()

        summary = {
            "run_id": run_id,
            "status": "completed",
            "n_anomalies": training_output["n_anomalies"],
            "anomaly_rate": training_output["anomaly_rate"],
            "total_cases": len(features_df),
        }
        logger.info("Training complete: %s", summary)
        return summary

    except Exception as exc:
        logger.exception("Training failed for run %d", run_id)
        # Mark as failed in DB
        try:
            run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
            if run:
                run.status = "failed"
                run.error_message = str(exc)[:1000]
                run.completed_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            db.rollback()
        return {"error": str(exc)}

    finally:
        db.close()
