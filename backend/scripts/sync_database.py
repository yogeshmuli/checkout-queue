from app.core.database import sync_database


if __name__ == "__main__":
    sync_database()
    print("Database tables synced successfully.")
