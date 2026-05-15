# Checkout Queue Backend

FastAPI backend skeleton for the Checkout Queue App.

## Run Locally

Create `.env` from `.env.example` and update `DATABASE_URL` with your PostgreSQL credentials.

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Health check:

```text
GET http://localhost:8000/api/v1/health
```

Default PostgreSQL connection format:

```text
postgresql+psycopg2://checkout_user:checkout_password@localhost:5432/checkout_queue
```

## Database Migrations

```bash
alembic upgrade head
```

For a direct SQLAlchemy metadata sync during early development:

```bash
python -m scripts.sync_database
```

To clean all table data while keeping schema and migrations metadata:

```bash
python -m scripts.clean_all_data
```
