"""
User schemas for request/response validation
Re-export shared SQLModel schemas with additional validation for API compatibility.
"""

from pydantic import validator
from apps.shared.models import UserCreate as BaseUserCreate, UserRead, UserUpdate

# Re-export the shared schemas
UserResponse = UserRead


class UserCreate(BaseUserCreate):
    """Enhanced user creation schema with additional validation."""
    confirm_password: str
    
    @validator('confirm_password')
    def passwords_match(cls, v, values, **kwargs):
        if 'password' in values and v != values['password']:
            raise ValueError('passwords do not match')
        return v
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('username must be alphanumeric (underscores and hyphens allowed)')
        if len(v) < 3:
            raise ValueError('username must be at least 3 characters long')
        return v 