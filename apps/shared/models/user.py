"""
User models using SQLModel for database tables and API schemas.
"""

from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime
from sqlalchemy.sql import func


class UserBase(SQLModel):
    """Base user model with common fields."""
    email: str = Field(unique=True, index=True, max_length=255)
    username: str = Field(unique=True, index=True, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    avatar_url: Optional[str] = Field(default=None)


class User(UserBase, table=True):
    """User table model."""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str = Field(max_length=255)
    created_at: Optional[datetime] = Field(
        default=None, 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    )
    
    def dict(self):
        """Convert user to dictionary (excluding password) for compatibility."""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
            "avatar_url": self.avatar_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UserCreate(UserBase):
    """Schema for creating a user."""
    password: str = Field(min_length=8)


class UserUpdate(SQLModel):
    """Schema for updating a user."""
    email: Optional[str] = Field(default=None, max_length=255)
    username: Optional[str] = Field(default=None, max_length=100)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = Field(default=None)
    is_superuser: Optional[bool] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)
    password: Optional[str] = Field(default=None, min_length=8)


class UserRead(UserBase):
    """Schema for reading a user (public fields only)."""
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None 