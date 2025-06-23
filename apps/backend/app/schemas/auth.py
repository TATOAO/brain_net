"""
Authentication schemas for request/response validation
"""

from pydantic import BaseModel, EmailStr
from typing import Optional


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Schema for token data."""
    email: Optional[str] = None
    user_id: Optional[int] = None


class RefreshToken(BaseModel):
    """Schema for refresh token request."""
    refresh_token: str 