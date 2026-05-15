from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import (
    AuthResponse,
    LogoutRequest,
    MessageResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(payload: UserRegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return AuthService(db).register_user(payload)


@router.post("/login", response_model=AuthResponse)
def login(payload: UserLoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return AuthService(db).login_user(payload)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.post("/logout", response_model=MessageResponse)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> MessageResponse:
    AuthService(db).logout_user(payload.refresh_token)
    return MessageResponse(message="Logged out successfully")

