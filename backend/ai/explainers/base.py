"""
ai/explainers/base.py
─────────────────────
Abstract base class and shared data structures for the Explainable AI
module (PRD Module 7).

Design principles
─────────────────
• Each explainer is an independent, pluggable unit.
• The orchestrator (``CompositeExplainer``) aggregates results.
• New explainers can be added without modifying existing code
  (open/closed principle).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


# ── Shared data structures ────────────────────────────────────────────────────

@dataclass
class Explanation:
    """A single human-readable explanation for an anomaly."""
    rule: str                    # short identifier, e.g. "skipped_approval"
    description: str             # human-readable sentence
    severity: str = "warning"    # "low" | "warning" | "high"
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class CaseExplanation:
    """All explanations for a single anomalous case."""
    case_id: str
    is_anomaly: bool
    anomaly_score: float
    explanations: list[Explanation]
    summary: str = ""            # auto-generated one-liner
    severity_score: int = 0      # 0–10, higher = more severe


# ── Abstract explainer ────────────────────────────────────────────────────────

class BaseExplainer(ABC):
    """
    Interface that every explainer must implement.

    The ``dataset_stats`` dict is pre-computed once per dataset and
    shared across all explainers (avoids redundant computation).
    """

    @abstractmethod
    def explain(
        self,
        case_events: list[dict],
        case_id: str,
        dataset_stats: dict[str, Any],
    ) -> list[Explanation]:
        """
        Generate explanations for a single case.

        Parameters
        ----------
        case_events : list[dict]
            Ordered events for this case (each dict has at minimum
            ``activity``, ``timestamp``, ``resource``, ``duration_seconds``).
        case_id : str
            The case identifier.
        dataset_stats : dict
            Pre-computed dataset-wide statistics (see statistics.py).

        Returns
        -------
        list[Explanation]
            Zero or more explanations.  Empty list means this rule
            didn't fire for this case.
        """
        ...

    @property
    def name(self) -> str:
        return self.__class__.__name__
