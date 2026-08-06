# Checkout Queue Codebase and Configuration Guide

## 1. Purpose

This guide is a practical introduction to the Checkout Queue repository. It explains:

- Where the main backend and frontend code lives.
- The major product capabilities.
- Which environment flags are available and what they change.
- How to switch analytics history between static and real data.
- How to enable or disable Checkout Queue, Quick Trial, demo tools, scheduled jobs, and mock SMS failures.
- Common development and operations questions.

For a detailed API and user-story inventory, see [FEATURE_TRACKER.md](FEATURE_TRACKER.md). For architecture and technology decisions, see [TECHNICAL_STACK_AND_ARCHITECTURE.md](TECHNICAL_STACK_AND_ARCHITECTURE.md).

## 2. Repository Structure

```text
checkout-que/
├── backend/
│   ├── app/
│   │   ├── core/           # Settings, database, security, and scheduler
│   │   ├── models/         # SQLAlchemy PostgreSQL models
│   │   ├── repositories/   # Database queries and persistence
│   │   ├── routes/         # FastAPI endpoints and HTTP concerns
│   │   ├── schemas/        # Pydantic request/response models
│   │   ├── scripts/        # Application maintenance scripts
│   │   ├── services/       # Business logic and orchestration
│   │   └── main.py         # FastAPI application startup
│   ├── alembic/            # Database migrations
│   ├── tests/              # Pytest test suite
│   ├── .env.example        # Backend configuration example
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/            # Axios client and API modules
│   │   ├── app/
│   │   │   ├── checkout/   # Checkout admin, staff, and customer UI
│   │   │   ├── trial/      # Quick Trial admin, staff, and customer UI
│   │   │   └── common/     # Shared UI, login, navigation, and flags
│   │   ├── assets/         # Images and other bundled assets
│   │   ├── store/          # Zustand state stores
│   │   ├── styles/         # Global styling
│   │   ├── App.jsx         # Top-level routes
│   │   └── main.jsx        # React/PWA entry point
│   ├── .env.local          # Local Vite configuration
│   ├── package.json
│   └── vite.config.js
└── docs/                    # Product and engineering documentation
```

## 3. Backend Request Flow

The backend follows a three-layer application structure:

```text
HTTP request
    ↓
Route
    ↓
Service
    ↓
Repository
    ↓
SQLAlchemy model / PostgreSQL
```

### Routes

Files under `backend/app/routes/` define URLs, authentication dependencies, request schemas, response schemas, and HTTP status behavior. Routes should not contain business rules or direct database queries.

### Services

Files under `backend/app/services/` contain queue assignment, wait scheduling, lifecycle transitions, analytics, machine learning, notifications, and other business logic.

### Repositories

Files under `backend/app/repositories/` are the only application layer that should query or mutate the database directly.

### Models and schemas

- `backend/app/models/` defines database tables and relationships with SQLAlchemy.
- `backend/app/schemas/` defines validated API inputs and outputs with Pydantic.
- Alembic migrations in `backend/alembic/versions/` must remain aligned with model changes.

## 4. Frontend Request Flow

```text
React page/component
    ↓
Module API function
    ↓
Shared Axios client
    ↓
FastAPI endpoint
```

- `frontend/src/App.jsx` registers top-level public and module routes.
- `frontend/src/app/common/moduleConfig.js` reads frontend module flags.
- `frontend/src/api/httpClient.js` applies bearer authentication, global request progress, session-expiry handling, and shared API error formatting.
- Checkout and Trial each have separate `admin`, `staff`, and `customer` workspaces.
- The frontend is a Vite PWA. Environment variables exposed to browser code must start with `VITE_`.

## 5. High-Level Feature List

### Shared platform features

- Bearer-token login and refresh-token authentication.
- Role-based access for `SUPER_ADMIN`, `STORE_ADMIN`, `MANAGER`, `CASHIER`, `SUPPORT`, and Trial zone assistants.
- Store and staff management.
- Module-aware landing, login, and workspace routing.
- Store notification configuration and notification logs.
- Mock SMS delivery for called and next-soon notifications.
- Admin analytics with Live, History, and Foresights views.
- Database and uploaded Excel machine-learning training flows.
- PWA installation and service-worker updates.
- Optional demo-data tools for super administrators.

### Checkout Queue

- Store checkout sections and counters.
- Counter types, token prefixes, and basket-size allocation bands.
- Per-counter queues or optional shared section queues.
- Customer QR entry, token creation, mobile lookup, live status, cancellation, and move-last.
- Counter assignment, calling-time scheduling, queue position, and wait estimates.
- Staff counter console and admin queue operations.
- Store calendar, service-time configuration, Random Forest training, and Checkout analytics.

### Quick Trial

- Trial zones and studios.
- Zone gender rules and studio types.
- Shared zone queues with studio assignment when service begins.
- Customer QR entry, token creation, lookup, status, cancellation, and move-last.
- Trial assistant studio board and admin queue operations.
- Trial calendar, service-time configuration, separate Random Forest training, and Trial analytics.

## 6. Where Configuration Comes From

Backend settings are defined in `backend/app/core/config.py` and loaded from a `.env` file in the backend process's current working directory. The recommended local setup is:

```bash
cd backend
cp .env.example .env
```

Frontend settings are read by Vite from files such as `frontend/.env.local` or from deployment environment variables.

Important operational difference:

- Backend setting changes require restarting the FastAPI process because settings and route registration are evaluated at startup.
- Frontend `VITE_*` changes require restarting the Vite development server. In production, rebuild and redeploy the frontend because these values are compiled into the browser bundle.

Use lowercase `true` and `false` in environment files for consistency. Do not commit real database credentials, deployed secret keys, or other secrets.

## 7. Feature Flags and Their Impact

### Module flags

Backend and frontend module flags should be changed together.

| Module | Backend flag | Frontend flag |
| --- | --- | --- |
| Checkout Queue | `ENABLE_CHECKOUT_QUEUE` | `VITE_ENABLE_CHECKOUT_QUEUE` |
| Quick Trial | `ENABLE_TRIAL_QUEUE` | `VITE_ENABLE_TRIAL_QUEUE` |

Example: enable Checkout and disable Quick Trial.

`backend/.env`:

```dotenv
ENABLE_CHECKOUT_QUEUE=true
ENABLE_TRIAL_QUEUE=false
```

`frontend/.env.local` or frontend deployment environment:

```dotenv
VITE_ENABLE_CHECKOUT_QUEUE=true
VITE_ENABLE_TRIAL_QUEUE=false
```

Then restart the backend and rebuild/restart the frontend.

#### Backend impact

- `ENABLE_CHECKOUT_QUEUE=false` stops registration of Checkout queue, store-config, calendar, section, and counter routers.
- `ENABLE_TRIAL_QUEUE=false` stops registration of Trial analytics, zone, studio, config, calendar, and queue routers.
- ML routes remain registered while at least one of the two modules is enabled.
- Shared routes such as authentication, stores, staff, notifications, health, and the base Checkout analytics router are registered independently of these module flags.

#### Frontend impact

- A disabled module is removed from the landing-page module choices and context selector.
- The Change Context action disappears when only one module is enabled.
- Staff module choices are additionally restricted by their role and saved assignment.

Current limitation: the frontend flags control discovery and navigation, but `App.jsx` still registers both module route trees. A user who manually enters a disabled module URL may load its frontend screen, although calls to backend endpoints disabled by the corresponding backend flag will fail. For a complete module shutdown, always disable both frontend and backend flags; deployment-level route controls may also be used if direct URL blocking is required.

Do not set both modules to `false` unless intentionally running only the shared platform endpoints. The frontend currently falls back to Checkout as its default module identifier when no module is enabled, so an all-disabled frontend is not a supported normal user configuration.

### Demo tools

```dotenv
ENABLE_DEMO_TOOLS=false
```

| Value | Impact |
| --- | --- |
| `false` | Demo Tools API routes are not registered. Recommended for production. |
| `true` | Registers `/api/v1/demotools/...` endpoints for creating, checking, and deleting isolated demo ML data. Endpoints require `SUPER_ADMIN`. |

The frontend demo floating action button is based on the logged-in user's `SUPER_ADMIN` role, not a separate Vite flag. If the backend flag is off, the button can still render for a super administrator, but its Demo Tools requests will return not found. Keep this in mind when disabling demo tools.

### In-app scheduler

```dotenv
ENABLE_IN_APP_SCHEDULER=true
```

| Value | Impact |
| --- | --- |
| `true` | Starts APScheduler with the FastAPI process. |
| `false` | Does not run scheduled cleanup or next-soon notification scans inside this process. |

When enabled, the scheduler runs:

- Nightly active-queue cleanup at `NIGHTLY_QUEUE_CLEANUP_HOUR` and `NIGHTLY_QUEUE_CLEANUP_MINUTE`.
- A next-soon notification scan every minute.

All schedules use `SCHEDULER_TIMEZONE`.

Avoid enabling the in-app scheduler in multiple web-server replicas unless duplicate execution is controlled externally. Each process creates its own scheduler. In a multi-instance production deployment, prefer one dedicated scheduler process or an external job runner.

### Analytics history modes

```dotenv
CHECKOUT_ANALYTICS_HISTORY_MODE="static"
TRIAL_ANALYTICS_HISTORY_MODE="static"
```

Accepted values are exactly:

- `static`
- `real`

The flags are independent, so Checkout can use real history while Trial uses static history, or the reverse.

#### Static mode

For analytics requests where `days > 1`, the backend reads the bundled fixture:

```text
backend/app/static_analytics_data.json
```

This produces populated demonstration charts even if the selected store has little historical queue data. Store identity and the latest ML metadata still come from the database, but historical chart values come from the static fixture.

#### Real mode

For analytics requests where `days > 1`, the backend calculates history from actual PostgreSQL queue tokens, calendar events, counters/studios, and current store configuration. New or lightly used stores may display empty or zero-valued charts until enough activity exists.

#### Live and Foresights behavior

The frontend sends `days=1` for both Live and Foresights. The backend always uses real database data when `days=1`, regardless of the history-mode flag. Only the History view, which sends 7, 30, or 90 days, switches between static and real sources.

#### How to switch History to real data

In `backend/.env`:

```dotenv
CHECKOUT_ANALYTICS_HISTORY_MODE="real"
TRIAL_ANALYTICS_HISTORY_MODE="real"
```

Restart the backend. A frontend rebuild is not required because these are backend-only flags.

To restore demonstration history:

```dotenv
CHECKOUT_ANALYTICS_HISTORY_MODE="static"
TRIAL_ANALYTICS_HISTORY_MODE="static"
```

### Mock SMS failure switch

```dotenv
MOCK_SMS_SHOULD_FAIL=false
```

| Value | Impact |
| --- | --- |
| `false` | The mock SMS client treats sends as successful and notification logs become `SENT`. |
| `true` | The mock client deliberately raises an error so failure handling and `FAILED` notification logs can be tested. |

This flag does not connect a real SMS provider. The current notification service uses `MockSmsClient` in both modes.

## 8. Other Backend Settings

| Setting | Default | Impact |
| --- | ---: | --- |
| `DATABASE_URL` | Local PostgreSQL URL | PostgreSQL connection used by SQLAlchemy. There is no SQLite fallback. |
| `CORS_ORIGINS` | Local frontend origin | JSON list of browser origins allowed to call the API. Include scheme and host, for example `https://app.example.com`. |
| `SECRET_KEY` | Development placeholder | Signs JWTs. Replace it with a long random secret in every deployed environment. Changing it invalidates existing signed access tokens. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `600` | Lifetime of bearer access tokens. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `30` | Lifetime of refresh tokens. Refresh tokens are stored as hashes. |
| `ML_MODEL_DIR` | `ml_models` | Base directory for Checkout and Trial model artifacts. Relative paths depend on the backend process working directory. Use persistent storage in production. |
| `ML_MIN_TRAINING_SAMPLES` | `50` | Minimum completed database records or valid uploaded spreadsheet rows required to train a model. |
| `ML_TRAINING_UPLOAD_MAX_BYTES` | `10485760` | Maximum uploaded ML workbook size; default is 10 MiB. |
| `ML_TRAINING_UPLOAD_MAX_ROWS` | `10000` | Maximum number of uploaded training-data rows. |
| `NIGHTLY_QUEUE_CLEANUP_HOUR` | `0` | Cleanup hour in `SCHEDULER_TIMEZONE`. |
| `NIGHTLY_QUEUE_CLEANUP_MINUTE` | `5` | Cleanup minute in `SCHEDULER_TIMEZONE`. |
| `SCHEDULER_TIMEZONE` | `Asia/Kolkata` | Time zone used by scheduled jobs. Use a valid IANA name. |
| `API_PREFIX` | `/api/v1` | Prefix for all API routes and OpenAPI JSON. Changing it also requires updating the frontend API base URL. |

## 9. Frontend Environment Settings

| Setting | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Full API prefix used by Axios. If omitted, the frontend uses `/api/v1`; Vite proxies this path to `http://localhost:8000` during local development. |
| `VITE_PUBLIC_APP_URL` | Public frontend origin used when generating customer QR URLs. Use the externally reachable frontend URL. |
| `VITE_ENABLE_CHECKOUT_QUEUE` | Shows or hides Checkout Queue in frontend module discovery. Defaults to enabled when omitted. |
| `VITE_ENABLE_TRIAL_QUEUE` | Shows or hides Quick Trial in frontend module discovery. Defaults to enabled when omitted. |

The frontend boolean parser treats `false`, `0`, `off`, and `no` as false, ignoring letter case. Any other defined value is treated as true. Prefer explicit `true` or `false`.

## 10. Common Configuration Recipes

### Checkout-only deployment

Backend:

```dotenv
ENABLE_CHECKOUT_QUEUE=true
ENABLE_TRIAL_QUEUE=false
```

Frontend:

```dotenv
VITE_ENABLE_CHECKOUT_QUEUE=true
VITE_ENABLE_TRIAL_QUEUE=false
```

### Trial-only deployment

Backend:

```dotenv
ENABLE_CHECKOUT_QUEUE=false
ENABLE_TRIAL_QUEUE=true
```

Frontend:

```dotenv
VITE_ENABLE_CHECKOUT_QUEUE=false
VITE_ENABLE_TRIAL_QUEUE=true
```

### Production-style safety settings

```dotenv
ENABLE_DEMO_TOOLS=false
MOCK_SMS_SHOULD_FAIL=false
CHECKOUT_ANALYTICS_HISTORY_MODE="real"
TRIAL_ANALYTICS_HISTORY_MODE="real"
```

Also provide a production PostgreSQL `DATABASE_URL`, a strong `SECRET_KEY`, correct `CORS_ORIGINS`, persistent `ML_MODEL_DIR` storage, and the intended scheduler strategy.

### Demo dashboard with populated history

```dotenv
CHECKOUT_ANALYTICS_HISTORY_MODE="static"
TRIAL_ANALYTICS_HISTORY_MODE="static"
```

This affects only multi-day History requests. Live operational values remain real.

## 11. Running and Verifying Locally

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 -m alembic upgrade head
uvicorn app.main:app --reload
```

Health check:

```text
GET http://localhost:8000/api/v1/health
```

Backend tests:

```bash
cd backend
python3 -m pytest tests
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

## 12. Frequently Asked Questions

### I changed a backend flag but nothing changed. Why?

Restart FastAPI. Backend settings are cached, and conditional API routers are registered only when the application starts. Also confirm that the `.env` file is being loaded from the process's working directory.

### I changed a `VITE_*` flag but the deployed UI did not change. Why?

Vite substitutes environment values during build. Rebuild and redeploy the frontend. For local development, restart `npm run dev`.

### Why does Live still show real values when History mode is `static`?

That is intentional. Live and Foresights request one day, and the backend always uses real data for `days=1`. Static mode is applied only when the analytics request covers more than one day.

### Why is real History empty or mostly zero?

Real mode reads actual queue-token history for the selected store and period. Verify that the selected store has tokens within the last 7, 30, or 90 days and that lifecycle timestamps such as completion and cancellation times were recorded.

### Can Checkout History and Trial History use different sources?

Yes. Set `CHECKOUT_ANALYTICS_HISTORY_MODE` and `TRIAL_ANALYTICS_HISTORY_MODE` independently.

### Why can I still open a hidden module by typing its URL?

The current frontend flags hide modules from normal discovery but do not remove their React route trees. Pair the frontend flag with the matching backend flag. The disabled backend module endpoints will not be registered, preventing normal operation.

### Why do API requests return 404 after disabling a module?

That is the expected backend behavior. Module-specific routers are not registered when their backend flag is false.

### Why are ML predictions falling back to rule-based service time?

Queue joining uses ML only when the store has a latest compatible model with `READY` status and a readable model artifact, and prediction succeeds. Otherwise it uses the store's base, per-item, and minimum service-time configuration and records `RULE_BASED` as the calculation method.

### Why did my trained ML model disappear after deployment?

Model metadata is stored in PostgreSQL, but model artifact files are stored under `ML_MODEL_DIR`. If that directory is on ephemeral deployment storage, the files can disappear during restart or redeployment. Configure persistent storage and keep the database metadata and artifact directory consistent.

### Should `sync_database` replace Alembic migrations?

No. `backend/app/core/database.py::sync_database` calls SQLAlchemy metadata creation and is intended only for development synchronization. Use Alembic migrations for controlled schema changes.

### What happens during nightly cleanup?

The job cancels active Checkout and Trial tokens and resets Checkout counter and Trial studio availability. Its schedule is controlled by the cleanup hour, cleanup minute, and scheduler time zone settings.

### How do I test notification failure behavior?

Set `MOCK_SMS_SHOULD_FAIL=true`, restart the backend, trigger a notification, and inspect notification logs. Restore it to `false` after testing.

### Where should a new backend feature be added?

Implement it as a thin vertical slice:

1. Add or update SQLAlchemy models and Alembic migrations if persistence changes.
2. Add Pydantic request and response schemas.
3. Add repository database operations.
4. Add service business logic.
5. Add route-level HTTP and authorization handling.
6. Add tests.
7. Update `docs/FEATURE_TRACKER.md`; update the architecture document if the structure or major design changes.

### Where should a new frontend feature be added?

Place module-specific pages under `frontend/src/app/checkout/` or `frontend/src/app/trial/`, shared UI under `frontend/src/app/common/`, API calls under `frontend/src/api/`, and shared client state under `frontend/src/store/`. Keep route imports and frontend page names aligned with the repository naming conventions.

