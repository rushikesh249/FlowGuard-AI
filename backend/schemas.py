from datetime import datetime
from pydantic import BaseModel, EmailStr
from models import Role

class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str
    role: Role = Role.Analyst

class UserResponse(UserBase):
    id: int
    role: Role
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None

class PasswordReset(BaseModel):
    current_password: str
    new_password: str

# ── Module 2: Upload & Validation ────────────────────────────────────────────

class UploadResponse(BaseModel):
    id: int
    filename: str
    original_name: str
    status: str               # "valid" | "invalid"
    total_traces: int | None
    total_events: int | None
    unique_activities: int | None
    errors: list[str]
    warnings: list[str]
    raw_path: str
    cleaned_path: str | None

    class Config:
        from_attributes = True

class UploadHistoryItem(BaseModel):
    id: int
    original_name: str
    status: str
    uploaded_at: datetime
    total_traces: int | None
    total_events: int | None
    unique_activities: int | None
    raw_path: str
    cleaned_path: str | None

    class Config:
        from_attributes = True


# ── Module 3: Process Mining ─────────────────────────────────────────────────

class ProcessNode(BaseModel):
    id: str
    label: str
    count: int
    is_start: bool
    is_end: bool


class ProcessEdge(BaseModel):
    source: str
    target: str
    count: int
    avg_duration_seconds: float | None = None


class ActivityStats(BaseModel):
    count: int
    first_occurrence: str | None = None
    last_occurrence: str | None = None
    avg_duration_seconds: float | None = None
    median_duration_seconds: float | None = None
    p90_duration_seconds: float | None = None
    resources: list[str] = []
    resource_counts: dict[str, int] = {}
    departments: list[str] = []


class ProcessMetadata(BaseModel):
    total_activities: int
    total_transitions: int
    total_events: int


class ProcessGraphResponse(BaseModel):
    nodes: list[ProcessNode]
    edges: list[ProcessEdge]
    activity_stats: dict[str, ActivityStats]
    metadata: ProcessMetadata


class CaseActivity(BaseModel):
    activity: str | None = None
    timestamp: str | None = None
    resource: str | None = None
    duration_seconds: float = 0
    Vendor: str | None = None
    Document_Type: str | None = None
    Company: str | None = None


class CaseDetailResponse(BaseModel):
    case_id: str
    activities: list[CaseActivity]


# ── Module 5/6: Anomaly Detection ───────────────────────────────────────────

class TrainAnomalyRequest(BaseModel):
    upload_id: int
    algorithm: str = "isolation_forest"       # "isolation_forest" | "lof"
    contamination: float = 0.05               # 0.01 – 0.10


class AnomalyRunResponse(BaseModel):
    id: int
    upload_id: int
    status: str
    algorithm: str
    contamination: float
    n_anomalies: int | None = None
    anomaly_rate: float | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None

    class Config:
        from_attributes = True


class AnomalyCaseResult(BaseModel):
    case_id: str
    is_anomaly: bool
    anomaly_score: float
    confidence: float
    n_events: int
    n_unique_activities: int


class AnomalyResultsResponse(BaseModel):
    run: AnomalyRunResponse
    total_cases: int
    total_anomalies: int
    anomaly_rate: float
    results: list[AnomalyCaseResult]
