"""Authentication routes."""
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.auth.schemas import RegisterRequest, LoginRequest, UserResponse
from app.auth.service import register_user, authenticate_user, generate_tokens
from app.core.dependencies import get_current_user
from app.users.models import User

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """Register a new user."""
    try:
        user = register_user(db, request.email, request.password)
        return UserResponse(id=str(user.id), email=user.email)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=UserResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login and set authentication cookies."""
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    access_token, refresh_token = generate_tokens(user)
    
    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=15 * 60  # 15 minutes
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60  # 7 days
    )
    
    return UserResponse(id=str(user.id), email=user.email)


@router.post("/logout")
def logout(response: Response):
    """Logout by clearing authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current authenticated user information."""
    return UserResponse(id=str(current_user.id), email=current_user.email)
