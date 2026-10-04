"""
ai/explainers/rules.py
──────────────────────
Rule-based explainers for the Procure-to-Pay process.

Each rule checks a specific business-logic invariant that should hold
in a well-formed P2P workflow.  If violated, an Explanation is emitted
with a human-readable description.

Rules implemented
─────────────────
1. SkippedApproval    — no approval activity found in the case
2. PaymentWithoutPO   — payment appears without a preceding purchase order
3. OutOfOrderSequence — invoice processed before the purchase order
4. DuplicateActivity  — same activity occurs more than once consecutively
5. UnusualCaseLength  — case has abnormally few or many events
"""
from __future__ import annotations

from typing import Any

from .base import BaseExplainer, Explanation


# ── Keyword sets for matching BPI 2019 activity names ────────────────────────
# BPI 2019 activities contain substrings like "SRM:", "PO ", "Invoice",
# "Payment", "Approval", etc.  These sets allow fuzzy matching.

_APPROVAL_KEYWORDS   = {"approval", "approve", "approved"}
_PAYMENT_KEYWORDS    = {"payment", "pay", "paid", "clearing"}
_PO_KEYWORDS         = {"purchase order", "po ", "po:", "purchase_order"}
_INVOICE_KEYWORDS    = {"invoice", "inv.", "inv "}
_RECEIPT_KEYWORDS    = {"goods receipt", "gr ", "receipt"}


def _activity_matches(activity: str, keywords: set[str]) -> bool:
    """Case-insensitive check if *activity* contains any keyword."""
    lower = activity.lower()
    return any(kw in lower for kw in keywords)


def _has_activity(events: list[dict], keywords: set[str]) -> bool:
    return any(_activity_matches(e.get("activity", ""), keywords) for e in events)


def _first_index(events: list[dict], keywords: set[str]) -> int:
    """Index of first event matching keywords, or -1."""
    for i, e in enumerate(events):
        if _activity_matches(e.get("activity", ""), keywords):
            return i
    return -1


# ── Rule 1: Skipped Approval ─────────────────────────────────────────────────

class SkippedApprovalExplainer(BaseExplainer):
    """Flag cases where no approval activity is present."""

    def explain(self, case_events, case_id, dataset_stats):
        if not _has_activity(case_events, _APPROVAL_KEYWORDS):
            return [Explanation(
                rule="skipped_approval",
                description="This case has no approval activity — "
                            "approval may have been skipped.",
                severity="high",
                details={"n_events": len(case_events)},
            )]
        return []


# ── Rule 2: Payment Without PO ───────────────────────────────────────────────

class PaymentWithoutPOExplainer(BaseExplainer):
    """Flag cases where a payment appears without a preceding purchase order."""

    def explain(self, case_events, case_id, dataset_stats):
        has_payment = _has_activity(case_events, _PAYMENT_KEYWORDS)
        has_po      = _has_activity(case_events, _PO_KEYWORDS)

        if has_payment and not has_po:
            return [Explanation(
                rule="payment_without_po",
                description="Payment was processed without a matching "
                            "Purchase Order.",
                severity="high",
                details={},
            )]
        return []


# ── Rule 3: Out-of-Order Sequence ────────────────────────────────────────────

class OutOfOrderSequenceExplainer(BaseExplainer):
    """Flag cases where an invoice appears before the purchase order."""

    def explain(self, case_events, case_id, dataset_stats):
        po_idx  = _first_index(case_events, _PO_KEYWORDS)
        inv_idx = _first_index(case_events, _INVOICE_KEYWORDS)

        if inv_idx >= 0 and po_idx >= 0 and inv_idx < po_idx:
            return [Explanation(
                rule="out_of_order_sequence",
                description="Invoice was processed before the Purchase "
                            f"Order (invoice at step {inv_idx + 1}, "
                            f"PO at step {po_idx + 1}).",
                severity="high",
                details={
                    "invoice_step": inv_idx + 1,
                    "po_step": po_idx + 1,
                },
            )]
        return []


# ── Rule 4: Duplicate Activity ───────────────────────────────────────────────

class DuplicateActivityExplainer(BaseExplainer):
    """Flag cases where the same activity occurs consecutively (re-work)."""

    def explain(self, case_events, case_id, dataset_stats):
        duplicates: list[str] = []
        for i in range(1, len(case_events)):
            if case_events[i].get("activity") == case_events[i - 1].get("activity"):
                act = case_events[i].get("activity", "unknown")
                if act not in duplicates:
                    duplicates.append(act)

        if duplicates:
            return [Explanation(
                rule="duplicate_activity",
                description=f"Activity repeated consecutively: "
                            f"{', '.join(duplicates[:3])}. "
                            "This may indicate rework or duplicate processing.",
                severity="warning",
                details={"duplicated_activities": duplicates[:5]},
            )]
        return []


# ── Rule 5: Unusual Case Length ──────────────────────────────────────────────

class UnusualCaseLengthExplainer(BaseExplainer):
    """Flag cases with abnormally few or many events compared to the dataset."""

    def explain(self, case_events, case_id, dataset_stats):
        n_events = len(case_events)
        avg = dataset_stats.get("avg_events_per_case")
        std = dataset_stats.get("std_events_per_case")
        median = dataset_stats.get("median_events_per_case")

        if avg is None or std is None or median is None:
            return []

        explanations: list[Explanation] = []

        if std > 0 and n_events < median * 0.3:
            explanations.append(Explanation(
                rule="unusually_short_case",
                description=(
                    f"This case has only {n_events} events, which is "
                    f"{n_events / median:.1f}x the median ({median:.0f}). "
                    "Steps may have been skipped."
                ),
                severity="warning",
                details={"n_events": n_events, "median": round(median, 1)},
            ))

        if std > 0 and n_events > avg + 3 * std:
            explanations.append(Explanation(
                rule="unusually_long_case",
                description=(
                    f"This case has {n_events} events — more than "
                    f"3 standard deviations above the mean ({avg:.0f} ± {std:.0f}). "
                    "This may indicate excessive rework or looping."
                ),
                severity="warning",
                details={"n_events": n_events, "mean": round(avg, 1), "std": round(std, 1)},
            ))

        return explanations
