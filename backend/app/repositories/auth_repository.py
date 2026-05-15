from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import RefreshToken, User, UserStoreAccess


class AuthRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user_by_email(self, email: str) -> User | None:
        statement = select(User).where(User.email == email.lower())
        return self.db.scalar(statement)

    def create_user(self, user: User) -> User:
        self.db.add(user)
        self.db.flush()
        return user

    def add_store_access(self, access: UserStoreAccess) -> UserStoreAccess:
        self.db.add(access)
        self.db.flush()
        return access

    def save_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        self.db.flush()
        return refresh_token

    def get_refresh_token_by_hash(self, token_hash: str) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return self.db.scalar(statement)

    def revoke_refresh_token(self, refresh_token: RefreshToken, revoked_at: datetime) -> RefreshToken:
        refresh_token.revoked_at = revoked_at
        self.db.flush()
        return refresh_token

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, instance: object) -> None:
        self.db.refresh(instance)

