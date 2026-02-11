from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    # No max length needed since we use SHA-256 + bcrypt which handles any length


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    # No max length needed since we use SHA-256 + bcrypt which handles any length


class UserResponse(BaseModel):
    id: str
    email: str

    class Config:
        from_attributes = True
