from sqlalchemy.orm import Session
from app.users.models import User
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token
)

def register_user(db: Session, email: str, password: str) -> User:
    """Register a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        raise ValueError("User with this email already exists")
    
    user = User(
        email=email,
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate a user by email and password."""
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


def generate_tokens(user: User) -> tuple[str, str]:
    """Generate access and refresh tokens for a user."""
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    return access_token, refresh_token
