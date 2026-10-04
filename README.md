# FlowGuard AI

**AI-Powered Process Mining and Anomaly Detection for Procure-to-Pay Workflows**

A full-stack application that analyzes procurement event logs to discover process flows, detect anomalies, and provide explainable AI insights — designed as a major semester project (4-student team).

---

## Quick Start (Docker)

```bash
cd docker/
docker compose up --build
```

First boot takes a few minutes: the backend waits for PostgreSQL, runs Alembic
migrations, and only then does the Celery worker start (the worker depends on a
healthy backend so migrations never race).

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

**Default credentials:** Create a new account directly in the UI at `/register` (choose Role: Admin, Manager, or Analyst), then sign in at `/login`. Password resets are available at `/reset-password`.

Clean teardown (removes the database and all uploaded data):

```bash
docker compose down -v
```

---

## Demo Walkthrough

1. **Register & login** — open http://localhost:3000, create an account, and sign in.
2. **Upload data** — go to *Upload Data* and upload `datasets/raw/BPI_Challenge_2019.xes`
   (728.56 MB on disk / ~144 MB compressed). Validation reports 251,734 traces / 1,595,923 events / 42 activities.
3. **Process view** — open *Process View* to see the reconstructed Procure-to-Pay
   directly-follows graph. Click any node for activity statistics.
4. **Train anomaly detection** — open *Anomaly Center*, select the upload, and
   start a training run (Isolation Forest, default 5% contamination). Training
   runs in the Celery worker; poll until status is `completed`.
5. **Inspect anomalies** — browse flagged cases, toggle All/Anomalies, and click a
   row to open the AI explanation panel (rule + statistical explanations, severity 0-10).
6. **Export reports** — open *Reports* and download Executive, Department,
   Anomaly, or Monthly reports as PDF or CSV.

---

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Next.js   │────▶│   FastAPI   │────▶│  PostgreSQL │
│  Frontend   │     │   Backend   │     │   Database  │
│   :3000     │     │    :8000    │     │    :5432    │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────▼──────┐     ┌─────────────┐
                    │   Celery    │────▶│    Redis     │
                    │   Worker    │     │   Broker    │
                    └─────────────┘     └─────────────┘
```

**5 services:** Frontend → Backend API → Database, with Celery worker for background anomaly detection tasks using Redis as message broker.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS, Recharts, React Flow |
| Backend | FastAPI, Pydantic, SQLAlchemy, Alembic |
| AI/ML | scikit-learn (Isolation Forest), PM4Py (XES parsing), pandas |
| Background Tasks | Celery + Redis |
| Database | PostgreSQL 15 |
| Containerization | Docker Compose |

---

## Project Structure

```
FlowGuard AI/
├── backend/
│   ├── ai/
│   │   ├── anomaly_detection.py    # Isolation Forest anomaly detector
│   │   ├── features.py             # Feature engineering (11 features/case)
│   │   ├── tasks.py                # Celery training task
│   │   └── explainers/             # Explainable AI module
│   │       ├── base.py             # Abstract explainer base class
│   │       ├── rules.py            # 5 rule-based explainers
│   │       └── statistics.py       # 3 statistical explainers
│   ├── alembic/                    # Database migrations
│   ├── reports/
│   │   ├── generator.py            # Report data computation
│   │   └── pdf_builder.py          # PDF rendering (fpdf2)
│   ├── routers/
│   │   ├── anomaly.py              # Anomaly detection endpoints
│   │   ├── explanations.py         # Explainable AI endpoints
│   │   ├── process_mining.py       # Process mining endpoints
│   │   ├── reports.py              # Report generation endpoints
│   │   └── upload.py               # File upload & validation
│   ├── main.py                     # FastAPI app entry point
│   ├── models.py                   # SQLAlchemy models
│   ├── process_mining.py           # DFG discovery engine
│   ├── validator.py                # XES validation & cleaning
│   └── security.py                 # JWT authentication
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── login/              # Login page
│       │   ├── dashboard/          # Analytics dashboard (KPIs, charts)
│       │   ├── upload/             # Drag-drop file upload
│       │   ├── process/            # Interactive process graph (React Flow)
│       │   ├── anomalies/          # Anomaly center with explanations
│       │   └── reports/            # Report download interface
│       ├── components/             # Sidebar, DashboardShell
│       └── lib/                    # API client, auth context, types
├── docker/
│   └── docker-compose.yml          # Full stack orchestration
└── datasets/                       # Sample data (BPI Challenge 2019)
```

---

## Features

### 1. Data Upload & Validation (Phase 2)
- **Supported Format:** `.xes` (IEEE 1849-2016 standard for process mining event logs). Preserves nested trace-level attributes (case attributes, vendor IDs, sub-spend areas) and timestamped event sequences.
- *Note:* Generic flat `.csv` ingestion is out of scope for this version as standard CSVs lack structured trace-event hierarchical schemas.
- Automatic validation: schema validation, mandatory attribute checks, ISO-8601 timestamp normalization, and deduplication.
- Deduplication & Cleaning: Raw BPI 2019 XES logs contain 1,595,923 events; validation removes 180,913 empty/duplicate records to produce a cleaned 1,415,010-event dataset for downstream graph discovery and ML.

### 2. Process Mining (Phase 3)
- Directly-Follows Graph (DFG) discovery using pure pandas
- Activity statistics (frequency, duration, p90 delay, resource distribution)
- Case-level drill-down with activity sequences
- Interactive React Flow graph visualization with dynamic edge-frequency threshold filtering

### 3. Anomaly Detection (Phase 4)
- Isolation Forest algorithm (scikit-learn)
- 11 engineered features per case (volume, duration, repetition, sequence)
- Background training via Celery + Redis (Role-based access: Admin & Manager)
- Paginated anomaly browsing with score filtering

### 4. Explainable AI (Phase 5)
- 8 pluggable explainers (open/closed principle):
  - **Rule-based:** Skipped approval, payment without PO, out-of-order sequence, duplicate activity, unusual case length
  - **Statistical:** Duration anomaly, resource anomaly, event count anomaly
- Composite severity scoring (0-10)
- Per-case explanation panel

### 5. Analytics Dashboard (Phase 6 & Tier B)
- **Executive KPIs:** Total Cases (251,734), Normal %, Anomalies Flagged, Unique Activities (42), Average Processing Time, Process Health Score.
- **Core Visualizations:** Anomaly Score Distribution histogram, Run Status & Model Metadata card.
- **Monthly Activity & Anomaly Trend:** Dual-layer area chart tracking event volume and flagged anomalies across time.
- **Department Delay & Anomaly Rates:** Ranked spend area performance table with duration and anomaly rate indicators (136 departments including a 3,289-case "Unassigned" bucket).
- **Top Vendors by Volume & Spend:** Supplier intelligence table ranking vendors by case count, total spend (€), and flagged anomaly counts.
- **Approval Bottleneck Analysis:** Granular metrics on PO approval throughput, average duration, 90th percentile delay, and workload distribution across top approver resources.
- **Flagged Anomalies Drill-down:** Top cases ranked by anomaly severity.

### 6. Report Generation (Phase 7)
- 4 report types: Executive Summary, Department, Anomaly, Monthly
- PDF and CSV export formats with optimized single-pass in-memory data generation
- Professional fintech-grade layout

---

## Dataset & Data Characteristics

**BPI Challenge 2019** — Real-world Procure-to-Pay event log (Large multinational manufacturing enterprise)

| Metric | Raw XES Value | Cleaned Dataset Value | Notes |
|--------|---------------|----------------------|-------|
| Cases / Traces | 251,734 | 251,734 | 100% trace preservation |
| Events | 1,595,923 | 1,415,010 | 180,913 duplicates/empty events cleaned |
| Unique Activities | 42 | 42 | Full workflow fidelity |
| Primary Time Range | 2018-01 — 2019-12 | 2018-01 — 2019-12 | >99.97% of all events |
| Timestamp Outliers | 318 events (0.02%) | 318 events (0.02%) | Legacy PO timestamps (pre-2018: 1948, 1993, 2001) |
| Departments | 136 areas | 136 areas | 248,445 assigned + 3,289 "Unassigned" cases |
| File Size | 728.56 MB (728,558,522 B) | ~82 MB (.csv) | IEEE 1849-2016 XML format |

> **Note on Event Counts:** Dashboard event counts and time-series totals reflect the deduplicated, validated dataset (**1,415,010 events**) to ensure exact mathematical consistency with ML feature vectors and downstream process graphs.

---

## Development (Local)

### Backend
```bash
cd backend/
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload --port 8000
```

### Celery Worker
```bash
cd backend/
celery -A celery_app.celery_app worker --loglevel=info
```

### Frontend
```bash
cd frontend/
npm install
npm run dev
```

### Prerequisites
- Python 3.11+
- Node.js 20+
- PostgreSQL 15
- Redis 7

---

## API Endpoints

| Module | Endpoint | Method | Description |
|--------|----------|--------|-------------|
| Auth | `/auth/register` | POST | Create account |
| Auth | `/auth/login` | POST | JWT login |
| Upload | `/upload/xes` | POST | Upload & validate XES |
| Upload | `/upload/history` | GET | List uploads |
| Process | `/process-mine/graph?upload_id=` | GET | Process graph + activity stats |
| Process | `/process-mine/case/{case_id}?upload_id=` | GET | Case activity sequence |
| Anomaly | `/anomaly/train` | POST | Trigger training (Celery) |
| Anomaly | `/anomaly/status/{run_id}` | GET | Training run status |
| Anomaly | `/anomaly/runs?upload_id=` | GET | List all runs |
| Anomaly | `/anomaly/results/{run_id}` | GET | Per-case results |
| Explain | `/explanations/{run_id}` | GET | Explanations for all anomalies |
| Explain | `/explanations/{run_id}/case/{case_id}` | GET | Single case explanation |
| Reports | `/reports/executive/{upload_id}?format=pdf\|csv` | GET | Executive report |
| Reports | `/reports/department/{upload_id}?format=pdf\|csv` | GET | Department report |
| Reports | `/reports/anomaly/{run_id}?format=pdf\|csv` | GET | Anomaly report |
| Reports | `/reports/monthly/{upload_id}?format=pdf\|csv` | GET | Monthly report |
| Reports | `/reports/data/department/{upload_id}` | GET | Department analytics JSON payload |
| Reports | `/reports/data/monthly/{upload_id}` | GET | Monthly trend analytics JSON payload |
| Reports | `/reports/data/vendors/{upload_id}` | GET | Vendor breakdown analytics JSON payload |

All endpoints except `/auth/*` and `/health` require a valid JWT Bearer token.
- **Tenancy Architecture:** Designed as a single-tenant enterprise platform where all authenticated users collaborate within the same organization.
- **Organization-Wide Shared Datasets:** Datasets, process mining graphs, anomaly models, and analytics are shared organization-wide rather than siloed per user.
- **Role-Based Access Control (RBAC):**
  - `Admin`: Full operational read/write access (upload datasets, trigger model training, view analytics, export reports).
  - `Manager`: Full operational read/write access (upload datasets, trigger model training, view analytics, export reports).
  - `Analyst`: Read-only access across all organizational datasets (view dashboards, explore process graphs, browse anomaly runs/explanations, export reports; write actions like upload and training return HTTP 403 Forbidden).

---

## Environment Variables

See [docker/.env.example](docker/.env.example) for all configuration options.

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection string |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis broker URL |
| `JWT_SECRET` | `flowguard-dev-secret` | JWT signing secret |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API URL |

---

## Team

Major semester project — 4 students

---

## License

Academic project — not for commercial use.
