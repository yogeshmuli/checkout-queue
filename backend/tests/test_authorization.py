from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from app.core.authorization import authorized_store_ids, ensure_store_access
from app.models.user import User, UserRole


def make_user(role: UserRole) -> User:
    return User(id=7, email="user@example.com", full_name="User", password_hash="hash", default_role=role)


def test_super_admin_has_global_store_access() -> None:
    assert authorized_store_ids(Mock(), make_user(UserRole.SUPER_ADMIN)) is None


def test_scoped_admin_uses_active_store_access_rows() -> None:
    db = Mock()
    db.scalars.return_value.all.return_value = [2, 5]
    user = make_user(UserRole.STORE_ADMIN)

    assert authorized_store_ids(db, user) == {2, 5}
    ensure_store_access(db, user, 5)

    with pytest.raises(HTTPException) as error:
        ensure_store_access(db, user, 9)
    assert error.value.status_code == 403


def test_scoped_admin_without_assignments_has_no_access() -> None:
    db = Mock()
    db.scalars.return_value.all.return_value = []

    with pytest.raises(HTTPException) as error:
        ensure_store_access(db, make_user(UserRole.MANAGER), 1)
    assert error.value.status_code == 403
