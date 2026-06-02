"""Remove all data from application tables while keeping the schema intact."""

from sqlalchemy import text

import app.models  # noqa: F401
from app.core.database import Base, SessionLocal
from scripts.create_superadmin import create_superadmin


def clean_all_data() -> None:
    """Truncate all mapped tables and reset identities.

    Keeps table definitions and migration metadata table intact.
    """
    db = SessionLocal()
    try:
        table_names = [table.name for table in Base.metadata.sorted_tables if table.name != "alembic_version"]
        if not table_names:
            print("No tables found to clean.")
            return

        quoted_tables = ", ".join(f'"{name}"' for name in table_names)
        db.execute(text(f"TRUNCATE TABLE {quoted_tables} RESTART IDENTITY CASCADE"))
        db.commit()
        create_superadmin()
        print("All application data has been cleaned. Tables were preserved.")
    except Exception as exc:
        db.rollback()
        print(f"Data cleanup failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    clean_all_data()
