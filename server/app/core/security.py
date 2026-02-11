from datetime import datetime, timedelta
from jose import jwt, JWTError
import bcrypt
import hashlib
from app.core.config import settings


def hash_password(password: str) -> str:
    sha256_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()

    salt = bcrypt.gensalt()
    # Convert SHA-256 hash to bytes for bcrypt
    sha256_bytes = sha256_hash.encode('utf-8')
    # Hash with bcrypt
    bcrypt_hash = bcrypt.hashpw(sha256_bytes, salt)
    
    # Return as string (bcrypt hash includes salt)
    return bcrypt_hash.decode('utf-8')


def verify_password(plain: str, hashed: str) -> bool:
    # Hash the plain password with SHA-256 first
    sha256_hash = hashlib.sha256(plain.encode('utf-8')).hexdigest()
    
    # Convert SHA-256 hash to bytes for bcrypt verification
    sha256_bytes = sha256_hash.encode('utf-8')
    
    # Verify the SHA-256 hash against the bcrypt hash
    try:
        return bcrypt.checkpw(sha256_bytes, hashed.encode('utf-8'))
    except Exception:
        return False


def create_access_token(data: dict) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """Create a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")
