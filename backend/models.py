import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, JSON, Float, ForeignKey
from database import Base

class Role(str, enum.Enum):
    Admin = "Admin"
    Manager = "Manager"
    Analyst = "Analyst"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(Role), default=Role.Analyst, nullable=False)
    is_active = Column(Boolean, default=True)

class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id              = Column(Integer, primary_key=True, index=True)
    filename        = Column(String, nullable=False)           # stored filename (uuid-prefixed)
    original_name   = Column(String, nullable=False)           # original upload filename
    status          = Column(String, nullable=False, default="pending")  # pending | valid | invalid
    uploaded_by     = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    total_traces    = Column(Integer, nullable=True)
    total_events    = Column(Integer, nullable=True)
    unique_activities = Column(Integer, nullable=True)
    validation_errors = Column(JSON, nullable=True)            # list of error strings
    raw_path        = Column(String, nullable=False)           # path to raw .xes file
    cleaned_path    = Column(String, nullable=True)            # path to cleaned .csv (if valid)


class AnomalyRun(Base):
    """Tracks one anomaly-detection training run for an uploaded dataset."""
    __tablename__ = "anomaly_runs"

    id              = Column(Integer, primary_key=True, index=True)
    upload_id       = Column(Integer, ForeignKey("uploaded_files.id"), nullable=False)
    status          = Column(String, nullable=False, default="pending")  # pending|running|completed|failed
    algorithm       = Column(String, nullable=False, default="isolation_forest")
    contamination   = Column(Float, nullable=False, default=0.05)
    n_anomalies     = Column(Integer, nullable=True)
    anomaly_rate    = Column(Float, nullable=True)
    model_path      = Column(String, nullable=True)   # path to pickled model
    results_path    = Column(String, nullable=True)   # path to results JSON
    started_at      = Column(DateTime, nullable=True)
    completed_at    = Column(DateTime, nullable=True)
    error_message   = Column(String, nullable=True)
