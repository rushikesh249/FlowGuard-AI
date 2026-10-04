import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from schemas import UserCreate, Role, AnomalyFilterParams

def test_user_create_valid():
    user = UserCreate(email="analyst@flowguard.ai", password="securepassword", role=Role.Analyst)
    assert user.email == "analyst@flowguard.ai"
    assert user.role == Role.Analyst

def test_user_create_invalid_email():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email", password="securepassword", role=Role.Analyst)

def test_anomaly_filter_defaults():
    params = AnomalyFilterParams()
    assert params.page == 1
    assert params.page_size == 50
    assert params.severity is None
