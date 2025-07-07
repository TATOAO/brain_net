"""
Sandbox authentication service for secure service-to-service communication.
"""

import jwt
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from fastapi import HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.logging import LoggerMixin
from app.core.database import DatabaseManager
from app.services.permissions import PermissionManager
from apps.shared.models import User


class SandboxAuthService(LoggerMixin):
    """Manages authentication and authorization for sandbox containers."""
    
    def __init__(self, db_manager: DatabaseManager, permission_manager: PermissionManager):
        self.db_manager = db_manager
        self.permission_manager = permission_manager
        self.active_tokens = {}  # In production, use Redis
        self.token_expiry_hours = 1
        
    async def create_execution_token(self, user_id: int, execution_id: str, 
                                   pipeline_id: Optional[int] = None,
                                   processor_id: Optional[int] = None,
                                   permissions: Optional[Dict] = None) -> str:
        """Create a temporary execution token for sandbox operations."""
        
        # Get user permissions
        user_permissions = await self.permission_manager.get_user_permissions(user_id)
        
        # Create token payload
        token_data = {
            "user_id": user_id,
            "execution_id": execution_id,
            "pipeline_id": pipeline_id,
            "processor_id": processor_id,
            "permissions": permissions or user_permissions,
            "issued_at": datetime.utcnow().isoformat(),
            "expires_at": (datetime.utcnow() + timedelta(hours=self.token_expiry_hours)).isoformat(),
            "scope": "database_access",
            "token_type": "execution",
            "jti": str(uuid.uuid4())  # JWT ID for token tracking
        }
        
        # Create JWT token
        token = jwt.encode(token_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Store token for validation and revocation
        self.active_tokens[token] = {
            "user_id": user_id,
            "execution_id": execution_id,
            "created_at": datetime.utcnow(),
            "expires_at": datetime.utcnow() + timedelta(hours=self.token_expiry_hours),
            "revoked": False
        }
        
        self.logger.info(f"Created execution token for user {user_id}, execution {execution_id}")
        
        return token
    
    async def validate_execution_token(self, token: str) -> Dict:
        """Validate and decode execution token."""
        
        try:
            # Decode JWT token
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Check if token is in active tokens
            if token not in self.active_tokens:
                raise HTTPException(status_code=401, detail="Token not found or expired")
            
            token_info = self.active_tokens[token]
            
            # Check if token is revoked
            if token_info.get("revoked", False):
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.utcnow() > expires_at:
                # Remove expired token
                del self.active_tokens[token]
                raise HTTPException(status_code=401, detail="Token expired")
            
            # Check scope
            if payload.get('scope') != 'database_access':
                raise HTTPException(status_code=401, detail="Invalid token scope")
            
            # Check token type
            if payload.get('token_type') != 'execution':
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError as e:
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    
    async def revoke_execution_token(self, token: str) -> bool:
        """Revoke an execution token."""
        
        if token in self.active_tokens:
            self.active_tokens[token]["revoked"] = True
            self.logger.info(f"Revoked execution token")
            return True
        
        return False
    
    async def revoke_user_tokens(self, user_id: int) -> int:
        """Revoke all tokens for a specific user."""
        
        revoked_count = 0
        for token, token_info in self.active_tokens.items():
            if token_info["user_id"] == user_id and not token_info.get("revoked", False):
                token_info["revoked"] = True
                revoked_count += 1
        
        self.logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
        return revoked_count
    
    async def revoke_execution_tokens(self, execution_id: str) -> int:
        """Revoke all tokens for a specific execution."""
        
        revoked_count = 0
        for token, token_info in self.active_tokens.items():
            if token_info["execution_id"] == execution_id and not token_info.get("revoked", False):
                token_info["revoked"] = True
                revoked_count += 1
        
        self.logger.info(f"Revoked {revoked_count} tokens for execution {execution_id}")
        return revoked_count
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens from memory."""
        
        now = datetime.utcnow()
        expired_tokens = []
        
        for token, token_info in self.active_tokens.items():
            if token_info["expires_at"] < now:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del self.active_tokens[token]
        
        self.logger.info(f"Cleaned up {len(expired_tokens)} expired tokens")
        return len(expired_tokens)
    
    async def get_active_tokens_count(self) -> int:
        """Get count of active tokens."""
        
        active_count = sum(1 for token_info in self.active_tokens.values() 
                          if not token_info.get("revoked", False))
        return active_count
    
    async def get_user_active_tokens(self, user_id: int) -> List[Dict]:
        """Get active tokens for a specific user."""
        
        user_tokens = []
        for token, token_info in self.active_tokens.items():
            if (token_info["user_id"] == user_id and 
                not token_info.get("revoked", False) and
                token_info["expires_at"] > datetime.utcnow()):
                
                user_tokens.append({
                    "execution_id": token_info["execution_id"],
                    "created_at": token_info["created_at"],
                    "expires_at": token_info["expires_at"]
                })
        
        return user_tokens


class SandboxAuthMiddleware:
    """Middleware for validating sandbox execution tokens."""
    
    def __init__(self, sandbox_auth_service: SandboxAuthService):
        self.sandbox_auth_service = sandbox_auth_service
    
    async def __call__(self, request: Request, call_next):
        """Middleware to validate database API requests."""
        
        # Check if this is a database API request
        if request.url.path.startswith('/api/v1/db/'):
            # Extract and validate token
            auth_header = request.headers.get('Authorization')
            if not auth_header or not auth_header.startswith('Bearer '):
                raise HTTPException(
                    status_code=401, 
                    detail="Missing or invalid authorization header"
                )
            
            token = auth_header.split(' ')[1]
            
            try:
                token_data = await self.sandbox_auth_service.validate_execution_token(token)
                
                # Add user context to request state
                request.state.user_id = token_data['user_id']
                request.state.execution_id = token_data['execution_id']
                request.state.pipeline_id = token_data.get('pipeline_id')
                request.state.processor_id = token_data.get('processor_id')
                request.state.permissions = token_data.get('permissions', {})
                request.state.token_data = token_data
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=401, 
                    detail=f"Token validation failed: {str(e)}"
                )
        
        response = await call_next(request)
        return response


# Security scheme for FastAPI
security = HTTPBearer()


async def get_current_sandbox_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    sandbox_auth_service: SandboxAuthService = Depends()
) -> Dict:
    """Dependency to get current user from sandbox token."""
    
    token = credentials.credentials
    token_data = await sandbox_auth_service.validate_execution_token(token)
    
    return {
        "user_id": token_data["user_id"],
        "execution_id": token_data["execution_id"],
        "permissions": token_data.get("permissions", {}),
        "token_data": token_data
    }


async def get_sandbox_auth_service(
    db_manager: DatabaseManager = Depends(),
    permission_manager: PermissionManager = Depends()
) -> SandboxAuthService:
    """Dependency to get sandbox auth service."""
    
    return SandboxAuthService(db_manager, permission_manager)


async def get_permission_manager(
    db_manager: DatabaseManager = Depends()
) -> PermissionManager:
    """Dependency to get permission manager."""
    
    return PermissionManager(db_manager)


class ExecutionTokenManager:
    """Manager for handling execution token lifecycle."""
    
    def __init__(self, sandbox_auth_service: SandboxAuthService):
        self.sandbox_auth_service = sandbox_auth_service
    
    async def create_pipeline_execution_token(self, user_id: int, pipeline_id: int, 
                                            execution_id: str) -> str:
        """Create token for pipeline execution."""
        
        return await self.sandbox_auth_service.create_execution_token(
            user_id=user_id,
            execution_id=execution_id,
            pipeline_id=pipeline_id,
            permissions=await self._get_pipeline_permissions(user_id, pipeline_id)
        )
    
    async def create_processor_execution_token(self, user_id: int, processor_id: int,
                                             execution_id: str) -> str:
        """Create token for processor execution."""
        
        return await self.sandbox_auth_service.create_execution_token(
            user_id=user_id,
            execution_id=execution_id,
            processor_id=processor_id,
            permissions=await self._get_processor_permissions(user_id, processor_id)
        )
    
    async def _get_pipeline_permissions(self, user_id: int, pipeline_id: int) -> Dict:
        """Get permissions for pipeline execution."""
        
        # This would typically check pipeline configuration to determine
        # what database operations are needed
        return {
            "postgres": ["SELECT", "INSERT", "UPDATE"],
            "elasticsearch": ["search", "index"],
            "neo4j": ["MATCH", "CREATE", "MERGE"],
            "redis": ["GET", "SET", "HGET", "HSET"]
        }
    
    async def _get_processor_permissions(self, user_id: int, processor_id: int) -> Dict:
        """Get permissions for processor execution."""
        
        # This would typically check processor configuration to determine
        # what database operations are needed
        return {
            "postgres": ["SELECT", "INSERT"],
            "elasticsearch": ["search"],
            "redis": ["GET", "SET"]
        } 