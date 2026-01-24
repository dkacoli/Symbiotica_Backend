from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID
class UserRole(str, Enum):
    GUEST = "GUEST"
    HOST = "HOST"
    ADMIN = "ADMIN"

# Request Models
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    full_name: str
    role: UserRole = UserRole.GUEST

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class ResetPasswordRequest(BaseModel):
    email: EmailStr

class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    role: Optional[UserRole] = None

# Response Models
class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds

class LoginResponse(BaseModel):
    user: UserResponse
    tokens: TokenResponse

class MessageResponse(BaseModel):
    message: str
    success: bool