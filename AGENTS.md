# Checkout Queue Agent Instructions

These instructions apply to this repository.

## Project Architecture

- Backend uses FastAPI with a three-layer structure:
  - `routes`
  - `services`
  - `repositories`
- SQLAlchemy ORM models live under `backend/app/models`.
- Pydantic schemas live under `backend/app/schemas`.
- Database access must go through repository classes.
- Business logic must live in service classes.
- Route files should handle HTTP concerns only.

## Database

- Use PostgreSQL as the application database.
- Do not introduce SQLite code paths, SQLite test setup, or SQLite fallback files.
- Keep Alembic migrations aligned with SQLAlchemy models.
- Use `backend/app/core/database.py::sync_database` only for development metadata sync.

## Authentication

- Admin and staff-facing APIs must use bearer-token authentication unless explicitly designed as public endpoints.
- Use role guards for protected admin APIs.
- Current roles are:
  - `SUPER_ADMIN`
  - `STORE_ADMIN`
  - `MANAGER`
  - `CASHIER`
  - `SUPPORT`
- Passwords must be stored only as salted hashes.
- Refresh tokens must be stored only as hashes.

## Documentation Tracking

- After implementing or changing any feature/API, update:
  - `docs/FEATURE_TRACKER.md`
- When architecture, stack, folder structure, or major design decisions change, update:
  - `docs/TECHNICAL_STACK_AND_ARCHITECTURE.md`
- The feature tracker should describe capabilities from a user-story/API point of view.

<!-- ## Testing

- Run backend tests before finishing backend changes: -->

```bash
cd backend
python3 -m pytest tests
```

- Avoid adding tests that require SQLite.
- Prefer unit tests with fakes/mocks unless a real PostgreSQL integration test is intentionally needed.

## Current Product Flow

The implemented product flow currently supports:

```text
Register/Login user -> Create/List/View/Update/Soft-delete stores -> Customer joins queue and receives token/wait time
```

Continue expanding the backend in thin vertical slices and update the tracker after each slice.

## Frontend Naming Conventions

These rules currently apply to `frontend/` only:

- In `pages` folders, do not use a `Page` suffix in file names or component names.
  - Use `CreateToken.jsx` + `CreateToken`, not `CreateTokenPage.jsx` + `CreateTokenPage`.
- Avoid redundant suffixes in frontend file names when the folder already conveys context.
  - Example: in `customer/utils`, prefer `customerUtils.js` over `customerPageUtils.js`.
- Keep route wiring and imports aligned with these names when creating or refactoring frontend modules.
