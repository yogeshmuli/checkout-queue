from app.core.database import SessionLocal
from app.models.user import User


def main() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "superadmin@example.com").first()
        if user is None:
            print("NOT_FOUND")
            return
        print(f"FOUND id={user.id} role={user.default_role.value} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
