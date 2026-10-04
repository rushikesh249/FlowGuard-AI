import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from ai.explainers.rules import (
    SkippedApprovalExplainer,
    PaymentWithoutPOExplainer,
    DuplicateActivityExplainer,
)

def test_skipped_approval_explainer():
    explainer = SkippedApprovalExplainer()
    # Case with purchase order creation followed by vendor payment without approval
    trace_events = [
        {"concept:name": "Create Purchase Order Item"},
        {"concept:name": "Record Goods Receipt"},
        {"concept:name": "Clear Invoice"},
    ]
    explanation = explainer.explain("case_101", trace_events, None)
    if explanation:
        assert explanation.rule_id == "RULE_SKIPPED_APPROVAL"
        assert explanation.severity > 0

def test_duplicate_activity_explainer():
    explainer = DuplicateActivityExplainer()
    trace_events = [
        {"concept:name": "Create Purchase Requisition"},
        {"concept:name": "Create Purchase Order Item"},
        {"concept:name": "Create Purchase Order Item"},  # duplicate
        {"concept:name": "Record Invoice Receipt"},
    ]
    explanation = explainer.explain("case_102", trace_events, None)
    assert explanation is not None
    assert explanation.rule_id == "RULE_DUPLICATE_ACTIVITY"
    assert "Create Purchase Order Item" in explanation.description
