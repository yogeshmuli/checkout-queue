from sqlalchemy.orm import Session
from app.models.store import Store
from app.core.database import SessionLocal
from app.models.checkout_section import CheckoutSection
from app.models.counter import Counter
from app.models.user import User, UserRole
from app.core.security import hash_password
from datetime import datetime, timezone

def seed():
    db: Session = SessionLocal()
    try:
        # Create a store
        store = Store(
            store_number="STORE-001",
            name="Main Store",
            address="123 Main St",
            manager_name="Alice",
            manager_phone="9876543210",
            spoc_name="Bob",
            spoc_phone="9876543211",
            is_active=True,
        )
        db.add(store)
        db.flush()  # Assigns store.id

        # Create a checkout section
        section = CheckoutSection(
            store_id=store.id,
            name="Default Section",
            section_type="GENERAL",
            is_active=True,
        )
        db.add(section)
        db.flush()  # Assigns section.id

        # Create a counter
        counter = Counter(
            section_id=section.id,
            counter_type="REGULAR",
            name="Counter 1",
            is_active=True,
            next_available_time=datetime.now(timezone.utc),
        )
        db.add(counter)
        db.flush()  # Assigns counter.id

        # Create an operational user with assignment details
        user = User(
            email="cashier@example.com",
            phone_number="9876543212",
            full_name="Charlie",
            password_hash=hash_password("cashier123"),
            default_role=UserRole.CASHIER,
            store_id=store.id,
            section_id=section.id,
            assigned_counter_id=counter.id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        print(f"Seeded store id={store.id}, section id={section.id}, counter id={counter.id}, user id={user.id}")
    except Exception as e:
        db.rollback()
        print(f"Seed failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()
