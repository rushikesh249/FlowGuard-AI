"""
backfill_explanations.py
────────────────────────
One-time script to backfill precomputed explanations into existing completed
AnomalyRun results.json files so legacy runs benefit from sub-millisecond
API response times without requiring a full model retrain.
"""
import json
import logging
import os
import sys
import time

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

from database import SessionLocal
from models import AnomalyRun, UploadedFile
from ai.anomaly_detection import load_results, save_results
from ai.explainers import attach_explanations_to_results


def backfill_run(run_id: int, db=None) -> bool:
    close_db = False
    if db is None:
        db = SessionLocal()
        close_db = True

    try:
        run = db.query(AnomalyRun).filter(AnomalyRun.id == run_id).first()
        if not run:
            logger.error("Run %d not found.", run_id)
            return False

        if run.status != "completed":
            logger.info("Run %d is not completed (status=%s). Skipping.", run_id, run.status)
            return False

        if not run.results_path or not os.path.exists(run.results_path):
            logger.error("Run %d results_path '%s' not found.", run_id, run.results_path)
            return False

        upload = db.query(UploadedFile).filter(UploadedFile.id == run.upload_id).first()
        if not upload or not upload.cleaned_path or not os.path.exists(upload.cleaned_path):
            logger.error("Run %d cleaned dataset not found for upload %s.", run_id, run.upload_id)
            return False

        logger.info("Loading results from %s ...", run.results_path)
        results = load_results(run.results_path)
        if not results:
            logger.warning("Run %d results file is empty.", run_id)
            return False

        # Check if already backfilled
        sample = results[0]
        if "explanations" in sample and "summary" in sample and "severity_score" in sample:
            logger.info("Run %d already has precomputed explanations attached. Nothing to do.", run_id)
            return True

        logger.info("Backfilling explanations for %d cases in Run %d ...", len(results), run_id)
        start_t = time.perf_counter()
        results = attach_explanations_to_results(results, upload.cleaned_path)
        elapsed = time.perf_counter() - start_t
        logger.info("Explanations generated in %.2f seconds. Writing back to %s ...", elapsed, run.results_path)

        # Atomic write
        tmp_path = run.results_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(results, f)
        os.replace(tmp_path, run.results_path)

        logger.info("Run %d backfill successfully completed in %.2fs!", run_id, elapsed)
        return True

    finally:
        if close_db:
            db.close()


def backfill_all():
    db = SessionLocal()
    try:
        runs = db.query(AnomalyRun).filter(AnomalyRun.status == "completed").all()
        logger.info("Found %d completed run(s) to check for backfill.", len(runs))
        for r in runs:
            backfill_run(r.id, db=db)
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_id = int(sys.argv[1])
        backfill_run(run_id)
    else:
        backfill_all()
