from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User, UserRole

SUPERADMIN_EMAIL = "superadmin@example.com"
SUPERADMIN_PASSWORD = "admin123"
SUPERADMIN_FULL_NAME = "Super Admin"


def main() -> None:
    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.email == SUPERADMIN_EMAIL).first()
        if existing is not None:
            print(f"ALREADY_EXISTS id={existing.id} role={existing.default_role.value} email={existing.email}")
            return

        user = User(
            email=SUPERADMIN_EMAIL,
            full_name=SUPERADMIN_FULL_NAME,
            password_hash=hash_password(SUPERADMIN_PASSWORD),
            default_role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"CREATED id={user.id} role={user.default_role.value} email={user.email}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
