import sys
from pathlib import Path
from datetime import timedelta

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from security import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from jose import jwt

def test_password_hashing():
    raw_password = "supersecretpassword123"
    hashed = get_password_hash(raw_password)
    assert hashed != raw_password
    assert verify_password(raw_password, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_jwt_token_creation():
    data = {"sub": "analyst@flowguard.ai", "role": "Analyst"}
    token = create_access_token(data=data, expires_delta=timedelta(minutes=15))
    assert isinstance(token, str)
    assert len(token) > 0

    decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "analyst@flowguard.ai"
    assert decoded["role"] == "Analyst"
    assert "exp" in decoded
