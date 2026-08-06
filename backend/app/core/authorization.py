from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User, UserRole, UserStoreAccess
from app.core.database import get_db
from app.core.security import require_roles


SCOPED_ADMIN_ROLES = {UserRole.STORE_ADMIN, UserRole.MANAGER}


def authorized_store_ids(db: Session, user: User) -> set[int] | None:
    """Return None for global access, otherwise the user's active store scope."""
    if user.default_role == UserRole.SUPER_ADMIN:
        return None
    if user.default_role in SCOPED_ADMIN_ROLES:
        # Keeps dependency-overridden unit tests usable; production always supplies a Session.
        if db is None:
            return {user.store_id} if user.store_id is not None else set()
        statement = select(UserStoreAccess.store_id).where(
            UserStoreAccess.user_id == user.id,
            UserStoreAccess.is_active.is_(True),
        )
        return set(db.scalars(statement).all())
    return {user.store_id} if user.store_id is not None else set()


def ensure_store_access(db: Session, user: User, store_id: int) -> None:
    store_ids = authorized_store_ids(db, user)
    if store_ids is not None and store_id not in store_ids:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Store access denied")


def scoped_store_id(db: Session, user: User, requested_store_id: int | None) -> tuple[int | None, set[int] | None]:
    store_ids = authorized_store_ids(db, user)
    if requested_store_id is not None:
        ensure_store_access(db, user, requested_store_id)
    return requested_store_id, store_ids


def require_store_roles(*allowed_roles: UserRole):
    def dependency(
        store_id: int,
        db: Session = Depends(get_db),
        user: User = Depends(require_roles(*allowed_roles)),
    ) -> User:
        ensure_store_access(db, user, store_id)
        return user

    return dependency
