from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.user import RefreshToken, User, UserStoreAccess
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import AuthResponse, TokenResponse, UserLoginRequest, UserRegisterRequest


class AuthService:
    def __init__(self, db: Session) -> None:
        self.repository = AuthRepository(db)

    def register_user(self, payload: UserRegisterRequest) -> AuthResponse:
        existing_user = self.repository.get_user_by_email(payload.email)
        if existing_user is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")

        user = User(
            email=payload.email.lower(),
            phone_number=payload.phone_number,
            full_name=payload.full_name,
            password_hash=hash_password(payload.password),
            default_role=payload.default_role,
            store_id=payload.store_id,
            section_id=payload.section_id,
            assigned_counter_id=payload.assigned_counter_id,
        )
        self.repository.create_user(user)

        if payload.store_id is not None:
            self.repository.add_store_access(
                UserStoreAccess(user_id=user.id, store_id=payload.store_id, role=payload.default_role)
            )

        tokens = self._create_tokens(user)
        self.repository.commit()
        self.repository.refresh(user)
        return AuthResponse(user=user, tokens=tokens)

    def login_user(self, payload: UserLoginRequest) -> AuthResponse:
        user = self.repository.get_user_by_email(payload.email)
        if user is None or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")

        user.last_login_at = datetime.now(timezone.utc)
        tokens = self._create_tokens(user)
        self.repository.commit()
        self.repository.refresh(user)
        return AuthResponse(user=user, tokens=tokens)

    def logout_user(self, refresh_token: str) -> None:
        token_hash = hash_refresh_token(refresh_token)
        stored_token = self.repository.get_refresh_token_by_hash(token_hash)
        if stored_token is None:
            return

        self.repository.revoke_refresh_token(stored_token, datetime.now(timezone.utc))
        self.repository.commit()

    def _create_tokens(self, user: User) -> TokenResponse:
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={
                "role": user.default_role.value,
                "email": user.email,
            },
        )
        refresh_token = generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.repository.save_refresh_token(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_refresh_token(refresh_token),
                expires_at=expires_at,
            )
        )
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in_minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )

