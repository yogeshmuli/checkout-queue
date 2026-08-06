from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.authorization import ensure_store_access
from app.core.security import hash_password
from app.models.user import User, UserRole, UserStoreAccess
from app.repositories.staff_repository import StaffRepository
from app.schemas.staff import StaffCreateRequest, StaffUpdateRequest


class StaffService:
    def __init__(self, db: Session) -> None:
        self.repository = StaffRepository(db)

    def create_staff(self, payload: StaffCreateRequest) -> User:
        self._ensure_email_available(payload.email)
        self._ensure_phone_available(payload.phone_number)
        self._validate_assignment(
            payload.store_id,
            payload.section_id,
            payload.assigned_counter_id,
            payload.assigned_zone_id,
            payload.default_role,
        )

        user = User(
            email=payload.email.lower(),
            phone_number=payload.phone_number,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            default_role=payload.default_role,
            store_id=payload.store_id,
            section_id=payload.section_id,
            assigned_counter_id=payload.assigned_counter_id,
            assigned_zone_id=payload.assigned_zone_id,
            is_active=payload.is_active,
        )
        self.repository.create_staff(user)
        self._sync_store_access(user, payload.store_id, payload.default_role)
        self.repository.commit()
        self.repository.refresh(user)
        return user

    def list_staff(
        self,
        include_inactive: bool = False,
        store_id: int | None = None,
        section_id: int | None = None,
        counter_id: int | None = None,
        zone_id: int | None = None,
        store_ids: set[int] | None = None,
    ) -> list[User]:
        kwargs = dict(
            include_inactive=include_inactive,
            store_id=store_id,
            section_id=section_id,
            counter_id=counter_id,
            zone_id=zone_id,
        )
        if store_ids is not None:
            kwargs["store_ids"] = store_ids
        return self.repository.list_staff(**kwargs)

    def get_staff(self, staff_id: int) -> User:
        user = self.repository.get_staff_by_id(staff_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff user not found")
        return user

    def update_staff(self, staff_id: int, payload: StaffUpdateRequest) -> User:
        user = self.get_staff(staff_id)
        update_data = payload.model_dump(exclude_unset=True)

        new_email = update_data.get("email")
        if new_email is not None and new_email.lower() != user.email:
            self._ensure_email_available(new_email, current_user_id=user.id)

        new_phone_number = update_data.get("phone_number")
        if new_phone_number is not None and new_phone_number != user.phone_number:
            self._ensure_phone_available(new_phone_number, current_user_id=user.id)

        new_role = update_data.get("default_role", user.default_role)
        if new_role == UserRole.TRIAL_ZONE_ASSISTANT:
            update_data["section_id"] = None
            update_data["assigned_counter_id"] = None
        else:
            update_data["assigned_zone_id"] = None

        new_store_id = update_data.get("store_id", user.store_id)
        new_section_id = update_data.get("section_id", user.section_id)
        new_counter_id = update_data.get("assigned_counter_id", user.assigned_counter_id)
        new_zone_id = update_data.get("assigned_zone_id", user.assigned_zone_id)
        self._validate_assignment(new_store_id, new_section_id, new_counter_id, new_zone_id, new_role)

        for field, value in update_data.items():
            if field == "password":
                if value is not None:
                    user.password_hash = hash_password(value)
            elif field == "email" and value is not None:
                user.email = value.lower()
            else:
                setattr(user, field, value)

        self._sync_store_access(user, user.store_id, user.default_role)
        self.repository.commit()
        self.repository.refresh(user)
        return user

    def deactivate_staff(self, staff_id: int) -> User:
        user = self.get_staff(staff_id)
        user.is_active = False
        self.repository.commit()
        self.repository.refresh(user)
        return user

    def _ensure_email_available(self, email: str, current_user_id: int | None = None) -> None:
        existing = self.repository.get_staff_by_email(email)
        if existing is not None and existing.id != current_user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")

    def _ensure_phone_available(self, phone_number: str | None, current_user_id: int | None = None) -> None:
        if phone_number is None:
            return
        existing = self.repository.get_staff_by_phone_number(phone_number)
        if existing is not None and existing.id != current_user_id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User phone number already exists")

    def _validate_assignment(
        self,
        store_id: int | None,
        section_id: int | None,
        assigned_counter_id: int | None,
        assigned_zone_id: int | None,
        role: UserRole,
    ) -> None:
        if assigned_counter_id is not None and assigned_zone_id is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Assign either counter or trial zone, not both")

        if role == UserRole.TRIAL_ZONE_ASSISTANT and assigned_zone_id is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TRIAL_ZONE_ASSISTANT must be assigned to trial zone")

        if role == UserRole.TRIAL_ZONE_ASSISTANT and (section_id is not None or assigned_counter_id is not None):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TRIAL_ZONE_ASSISTANT cannot be assigned to checkout section or counter")

        if store_id is not None and self.repository.get_store_by_id(store_id) is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Store not found")

        section = None
        if section_id is not None:
            section = self.repository.get_section_by_id(section_id)
            if section is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
            if store_id is not None and section.store_id != store_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Section does not belong to store")

        if assigned_counter_id is not None:
            counter = self.repository.get_counter_by_id(assigned_counter_id)
            if counter is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")
            if role == UserRole.TRIAL_ZONE_ASSISTANT:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TRIAL_ZONE_ASSISTANT cannot be assigned to checkout counter")
            if section_id is not None and counter.section_id != section_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Counter does not belong to section")
            if section_id is None and store_id is not None:
                counter_section = section or self.repository.get_section_by_id(counter.section_id)
                if counter_section is not None and counter_section.store_id != store_id:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Counter does not belong to store")

        if assigned_zone_id is not None:
            zone = self.repository.get_zone_by_id(assigned_zone_id)
            if zone is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial zone not found")
            if role != UserRole.TRIAL_ZONE_ASSISTANT:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only TRIAL_ZONE_ASSISTANT can be assigned to trial zone")
            if store_id is not None and zone.store_id != store_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Trial zone does not belong to store")

        # Role-to-assignment checks are enforced only when assignment fields are provided.

    def _sync_store_access(self, user: User, store_id: int | None, role: UserRole) -> None:
        for access in self.repository.list_store_access(user.id):
            access.is_active = store_id is not None and access.store_id == store_id
            if access.is_active:
                access.role = role

        if store_id is None:
            return

        access = self.repository.get_store_access(user.id, store_id)
        if access is None:
            self.repository.add_store_access(UserStoreAccess(user_id=user.id, store_id=store_id, role=role))
        else:
            access.role = role
            access.is_active = True
    def ensure_assignment_resource_access(
        self,
        current_user: User,
        section_id: int | None = None,
        counter_id: int | None = None,
        zone_id: int | None = None,
    ) -> None:
        if section_id is not None:
            section = self.repository.get_section_by_id(section_id)
            if section is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Section not found")
            ensure_store_access(self.repository.db, current_user, section.store_id)
        if counter_id is not None:
            counter = self.repository.get_counter_by_id(counter_id)
            section = self.repository.get_section_by_id(counter.section_id) if counter is not None else None
            if section is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Counter not found")
            ensure_store_access(self.repository.db, current_user, section.store_id)
        if zone_id is not None:
            zone = self.repository.get_zone_by_id(zone_id)
            if zone is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trial zone not found")
            ensure_store_access(self.repository.db, current_user, zone.store_id)
