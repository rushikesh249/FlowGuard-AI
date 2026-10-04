import sys
from pathlib import Path
import pandas as pd

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

def test_mining_edge_discovery():
    # Verify synthetic dataframe transition counting
    sample_data = {
        "case:concept:name": ["C1", "C1", "C1", "C2", "C2"],
        "concept:name": ["Start", "Approval", "End", "Start", "End"],
        "time:timestamp": pd.to_datetime([
            "2026-01-01 10:00:00",
            "2026-01-01 11:00:00",
            "2026-01-01 12:00:00",
            "2026-01-02 10:00:00",
            "2026-01-02 13:00:00",
        ]),
    }
    df = pd.DataFrame(sample_data)
    df["next_activity"] = df.groupby("case:concept:name")["concept:name"].shift(-1)
    transitions = df.dropna(subset=["next_activity"])
    
    assert len(transitions) == 3
    pair_counts = transitions.groupby(["concept:name", "next_activity"]).size()
    assert pair_counts[("Start", "Approval")] == 1
    assert pair_counts[("Approval", "End")] == 1
    assert pair_counts[("Start", "End")] == 1
