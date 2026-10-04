"""
ai/anomaly_detection.py
───────────────────────
Module 5/6 – Unsupervised Anomaly Detection Engine.

Wraps scikit-learn's Isolation Forest (with LOF as a fallback option).
Trains a FRESH model per uploaded dataset — never reuses a model across
datasets, because every organisation's "normal" is different.

Public API
──────────
train_model(features_df, contamination)  → fitted model + scores
predict_anomalies(features_df, model)    → per-case anomaly results
save_model / load_model                  → persistence to disk
"""
from __future__ import annotations

import json
import logging
import os
import pickle
from typing import Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)


# ── Training ─────────────────────────────────────────────────────────────────

def train_model(
    features_df: pd.DataFrame,
    contamination: float = 0.05,
    algorithm: str = "isolation_forest",
    random_state: int = 42,
) -> dict:
    """
    Train an unsupervised anomaly detection model on per-case features.

    Parameters
    ----------
    features_df : pd.DataFrame
        One row per case, all columns numerical (output of extract_features).
    contamination : float
        Expected proportion of anomalies (0.01 – 0.10 typical).
    algorithm : str
        "isolation_forest" (default) or "lof".
    random_state : int
        Reproducibility seed.

    Returns
    -------
    dict with keys:
        model            – fitted sklearn estimator
        scaler           – fitted StandardScaler
        anomaly_scores   – np.ndarray  (lower = more anomalous)
        predictions      – np.ndarray  (+1 normal, -1 anomaly)
        n_anomalies      – int
        anomaly_rate     – float
    """
    logger.info(
        "Training %s | %d cases × %d features | contamination=%.3f",
        algorithm, len(features_df), len(features_df.columns), contamination,
    )

    X = features_df.values

    # Standardise features (important for distance-based methods like LOF)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Select algorithm
    if algorithm == "lof":
        model = LocalOutlierFactor(
            n_neighbors=20,
            contamination=contamination,
            novelty=False,
        )
        predictions = model.fit_predict(X_scaled)  # +1 / -1
        # LOF doesn't expose score_samples in non-novelty mode easily;
        # use negative outlier factor as anomaly score
        anomaly_scores = model.negative_outlier_factor_
    else:
        # Default: Isolation Forest
        model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=100,
            n_jobs=-1,
        )
        model.fit(X_scaled)
        predictions = model.predict(X_scaled)  # +1 / -1
        anomaly_scores = model.decision_function(X_scaled)  # lower = more anomalous

    n_anomalies = int((predictions == -1).sum())
    anomaly_rate = n_anomalies / len(predictions) if len(predictions) else 0.0

    logger.info(
        "Training complete | anomalies=%d (%.1f%%)",
        n_anomalies, anomaly_rate * 100,
    )

    return {
        "model": model,
        "scaler": scaler,
        "anomaly_scores": anomaly_scores,
        "predictions": predictions,
        "n_anomalies": n_anomalies,
        "anomaly_rate": anomaly_rate,
    }


# ── Prediction / result formatting ───────────────────────────────────────────

def format_results(
    features_df: pd.DataFrame,
    predictions: np.ndarray,
    anomaly_scores: np.ndarray,
) -> list[dict]:
    """
    Combine case IDs, predictions, and scores into a list of per-case results.

    Returns
    -------
    list[dict]  — each dict has: case_id, is_anomaly, anomaly_score,
                  confidence, n_events, n_unique_activities
    """
    case_ids = features_df.index.tolist()

    # Convert decision_function score to a 0–1 "anomaly score" (higher = more anomalous)
    # decision_function: lower = more anomalous.  Invert and normalise to [0, 1].
    score_min = anomaly_scores.min()
    score_max = anomaly_scores.max()
    if score_max - score_min > 0:
        normalised = 1 - (anomaly_scores - score_min) / (score_max - score_min)
    else:
        normalised = np.zeros_like(anomaly_scores)

    results: list[dict] = []
    for i, case_id in enumerate(case_ids):
        is_anomaly = bool(predictions[i] == -1)
        results.append({
            "case_id": str(case_id),
            "is_anomaly": is_anomaly,
            "anomaly_score": round(float(normalised[i]), 4),
            "confidence": round(float(normalised[i]) if is_anomaly else float(1 - normalised[i]), 4),
            "n_events": int(features_df.iloc[i]["n_events"]),
            "n_unique_activities": int(features_df.iloc[i]["n_unique_activities"]),
        })

    # Sort: anomalies first, then by anomaly_score descending
    results.sort(key=lambda r: (-int(r["is_anomaly"]), -r["anomaly_score"]))
    return results


# ── Model persistence ────────────────────────────────────────────────────────

def save_model(model, scaler, output_dir: str, run_id: str) -> dict:
    """
    Save the fitted model and scaler to disk.

    Returns paths dict.
    """
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, f"{run_id}_model.pkl")
    scaler_path = os.path.join(output_dir, f"{run_id}_scaler.pkl")

    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    logger.info("Model saved to %s", model_path)
    return {"model_path": model_path, "scaler_path": scaler_path}


def load_model(model_path: str, scaler_path: str) -> tuple:
    """Load a previously saved model and scaler from disk."""
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    with open(scaler_path, "rb") as f:
        scaler = pickle.load(f)
    return model, scaler


def save_results(results: list[dict], output_dir: str, run_id: str) -> str:
    """Save per-case anomaly results as JSON.  Returns file path."""
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"{run_id}_results.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info("Results saved to %s (%d records)", path, len(results))
    return path


def load_results(results_path: str) -> list[dict]:
    """Load previously saved anomaly results from JSON."""
    with open(results_path, "r", encoding="utf-8") as f:
        return json.load(f)
