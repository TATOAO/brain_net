"""
Permission management system for database access control.
"""

import re
import sqlparse
from typing import Dict, List, Optional, Set
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import LoggerMixin
from app.core.database import DatabaseManager


class PermissionManager(LoggerMixin):
    """Manages user permissions for database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        
        # Define allowed operations per database type
        self.allowed_operations = {
            'postgres': {
                'SELECT': self._validate_postgres_select,
                'INSERT': self._validate_postgres_insert,
                'UPDATE': self._validate_postgres_update,
                'DELETE': self._validate_postgres_delete
            },
            'elasticsearch': {
                'search': self._validate_elasticsearch_search,
                'index': self._validate_elasticsearch_index,
                'delete': self._validate_elasticsearch_delete
            },
            'neo4j': {
                'MATCH': self._validate_neo4j_match,
                'CREATE': self._validate_neo4j_create,
                'MERGE': self._validate_neo4j_merge,
                'DELETE': self._validate_neo4j_delete
            },
            'redis': {
                'GET': self._validate_redis_get,
                'SET': self._validate_redis_set,
                'DEL': self._validate_redis_del,
                'LPUSH': self._validate_redis_lpush,
                'RPOP': self._validate_redis_rpop,
                'HGET': self._validate_redis_hget,
                'HSET': self._validate_redis_hset
            }
        }
        
        # Public tables accessible to all users
        self.public_tables = {
            'public_documents',
            'shared_resources',
            'system_settings',
            'built_in_processors'
        }
        
        # Tables that require admin access
        self.admin_tables = {
            'users',
            'user_permissions',
            'audit_logs',
            'system_configuration'
        }
        
        # Dangerous SQL functions that should be blocked
        self.dangerous_sql_functions = {
            'pg_sleep', 'pg_read_file', 'pg_ls_dir', 'pg_stat_file',
            'copy', 'lo_import', 'lo_export', 'dblink', 'pg_exec',
            'pg_terminate_backend', 'pg_cancel_backend'
        }
    
    async def can_execute_operation(self, user_id: int, database_type: str, 
                                  operation: str, query_or_command: str,
                                  context: Dict = None) -> tuple[bool, Optional[str]]:
        """Check if user can execute the given database operation."""
        
        context = context or {}
        
        # Check if database type is supported
        if database_type not in self.allowed_operations:
            return False, f"Database type '{database_type}' not supported"
        
        # Check if operation is allowed for this database type
        if operation not in self.allowed_operations[database_type]:
            return False, f"Operation '{operation}' not allowed for {database_type}"
        
        # Get validator function
        validator = self.allowed_operations[database_type][operation]
        
        # Execute validation
        try:
            is_allowed, reason = await validator(user_id, query_or_command, context)
            return is_allowed, reason
        except Exception as e:
            self.logger.error(f"Permission validation failed: {e}")
            return False, f"Permission validation error: {str(e)}"
    
    async def get_user_permissions(self, user_id: int) -> Dict[str, List[str]]:
        """Get user's permissions for all database types."""
        
        # This would typically query a permissions table
        # For now, return basic permissions
        return {
            'postgres': ['SELECT', 'INSERT', 'UPDATE', 'DELETE'],
            'elasticsearch': ['search', 'index'],
            'neo4j': ['MATCH', 'CREATE', 'MERGE'],
            'redis': ['GET', 'SET', 'LPUSH', 'RPOP', 'HGET', 'HSET']
        }
    
    async def is_admin_user(self, user_id: int) -> bool:
        """Check if user has admin privileges."""
        
        try:
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(
                    text("SELECT is_admin FROM users WHERE id = :user_id"),
                    {"user_id": user_id}
                )
                user_row = result.fetchone()
                return user_row and user_row[0] if user_row else False
        except Exception as e:
            self.logger.error(f"Error checking admin status: {e}")
            return False
    
    # PostgreSQL Validators
    async def _validate_postgres_select(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate PostgreSQL SELECT query."""
        
        # Parse SQL query
        try:
            parsed = sqlparse.parse(query)[0]
        except Exception as e:
            return False, f"Invalid SQL syntax: {str(e)}"
        
        # Extract tables being accessed
        tables = self._extract_postgres_tables(parsed)
        
        # Check dangerous functions
        if self._contains_dangerous_sql_functions(query):
            return False, "Query contains dangerous functions"
        
        # Check table access permissions
        for table in tables:
            if not await self._can_access_postgres_table(user_id, table, 'SELECT'):
                return False, f"No SELECT permission for table '{table}'"
        
        return True, None
    
    async def _validate_postgres_insert(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate PostgreSQL INSERT query."""
        
        parsed = sqlparse.parse(query)[0]
        tables = self._extract_postgres_tables(parsed)
        
        for table in tables:
            if not await self._can_access_postgres_table(user_id, table, 'INSERT'):
                return False, f"No INSERT permission for table '{table}'"
        
        return True, None
    
    async def _validate_postgres_update(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate PostgreSQL UPDATE query."""
        
        parsed = sqlparse.parse(query)[0]
        tables = self._extract_postgres_tables(parsed)
        
        # Check for WHERE clause (prevent mass updates)
        if not self._has_where_clause(parsed):
            return False, "UPDATE queries must include WHERE clause"
        
        for table in tables:
            if not await self._can_access_postgres_table(user_id, table, 'UPDATE'):
                return False, f"No UPDATE permission for table '{table}'"
        
        return True, None
    
    async def _validate_postgres_delete(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate PostgreSQL DELETE query."""
        
        parsed = sqlparse.parse(query)[0]
        tables = self._extract_postgres_tables(parsed)
        
        # Check for WHERE clause (prevent mass deletes)
        if not self._has_where_clause(parsed):
            return False, "DELETE queries must include WHERE clause"
        
        for table in tables:
            if not await self._can_access_postgres_table(user_id, table, 'DELETE'):
                return False, f"No DELETE permission for table '{table}'"
        
        return True, None
    
    # Elasticsearch Validators
    async def _validate_elasticsearch_search(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Elasticsearch search query."""
        
        index = context.get('index', '')
        
        # Check if user can access this index
        if not await self._can_access_elasticsearch_index(user_id, index):
            return False, f"No access to index '{index}'"
        
        return True, None
    
    async def _validate_elasticsearch_index(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Elasticsearch index operation."""
        
        index = context.get('index', '')
        
        # Only allow indexing to user-specific indices
        if not index.startswith(f'user_{user_id}_'):
            return False, f"Can only index to user-specific indices"
        
        return True, None
    
    async def _validate_elasticsearch_delete(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Elasticsearch delete operation."""
        
        index = context.get('index', '')
        
        # Only allow deleting from user-specific indices
        if not index.startswith(f'user_{user_id}_'):
            return False, f"Can only delete from user-specific indices"
        
        return True, None
    
    # Neo4j Validators
    async def _validate_neo4j_match(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Neo4j MATCH query."""
        
        # Check for user context in query
        if f"user_id: {user_id}" not in query and "user_id:" not in query:
            return False, "Neo4j queries must include user_id filter"
        
        return True, None
    
    async def _validate_neo4j_create(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Neo4j CREATE query."""
        
        # Ensure user_id is included in CREATE operations
        if f"user_id: {user_id}" not in query:
            return False, "Neo4j CREATE operations must include user_id"
        
        return True, None
    
    async def _validate_neo4j_merge(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Neo4j MERGE query."""
        
        if f"user_id: {user_id}" not in query:
            return False, "Neo4j MERGE operations must include user_id"
        
        return True, None
    
    async def _validate_neo4j_delete(self, user_id: int, query: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Neo4j DELETE query."""
        
        if f"user_id: {user_id}" not in query:
            return False, "Neo4j DELETE operations must include user_id filter"
        
        return True, None
    
    # Redis Validators
    async def _validate_redis_get(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis GET command."""
        
        args = context.get('args', [])
        if not args:
            return False, "Redis GET requires key argument"
        
        key = args[0]
        if not await self._can_access_redis_key(user_id, key):
            return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    async def _validate_redis_set(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis SET command."""
        
        args = context.get('args', [])
        if len(args) < 2:
            return False, "Redis SET requires key and value arguments"
        
        key = args[0]
        if not await self._can_access_redis_key(user_id, key):
            return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    async def _validate_redis_del(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis DEL command."""
        
        args = context.get('args', [])
        if not args:
            return False, "Redis DEL requires key argument"
        
        for key in args:
            if not await self._can_access_redis_key(user_id, key):
                return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    async def _validate_redis_lpush(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis LPUSH command."""
        
        args = context.get('args', [])
        if len(args) < 2:
            return False, "Redis LPUSH requires key and value arguments"
        
        key = args[0]
        if not await self._can_access_redis_key(user_id, key):
            return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    async def _validate_redis_rpop(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis RPOP command."""
        
        args = context.get('args', [])
        if not args:
            return False, "Redis RPOP requires key argument"
        
        key = args[0]
        if not await self._can_access_redis_key(user_id, key):
            return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    async def _validate_redis_hget(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis HGET command."""
        
        args = context.get('args', [])
        if len(args) < 2:
            return False, "Redis HGET requires key and field arguments"
        
        key = args[0]
        if not await self._can_access_redis_key(user_id, key):
            return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    async def _validate_redis_hset(self, user_id: int, command: str, context: Dict) -> tuple[bool, Optional[str]]:
        """Validate Redis HSET command."""
        
        args = context.get('args', [])
        if len(args) < 3:
            return False, "Redis HSET requires key, field, and value arguments"
        
        key = args[0]
        if not await self._can_access_redis_key(user_id, key):
            return False, f"No access to Redis key '{key}'"
        
        return True, None
    
    # Helper Methods
    async def _can_access_postgres_table(self, user_id: int, table_name: str, operation: str) -> bool:
        """Check if user can access PostgreSQL table."""
        
        # Public tables accessible to all users
        if table_name in self.public_tables:
            return True
        
        # Admin tables require admin access
        if table_name in self.admin_tables:
            return await self.is_admin_user(user_id)
        
        # User-specific tables
        if table_name.startswith(f'user_{user_id}_'):
            return True
        
        # Check explicit permissions in database
        try:
            async with self.db_manager.get_postgres_session() as session:
                result = await session.execute(
                    text("""
                        SELECT 1 FROM user_table_permissions 
                        WHERE user_id = :user_id 
                        AND table_name = :table_name 
                        AND operation = :operation
                    """),
                    {
                        "user_id": user_id,
                        "table_name": table_name,
                        "operation": operation
                    }
                )
                return result.fetchone() is not None
        except Exception as e:
            self.logger.error(f"Error checking table permissions: {e}")
            return False
    
    async def _can_access_elasticsearch_index(self, user_id: int, index: str) -> bool:
        """Check if user can access Elasticsearch index."""
        
        # Public indices
        if index.startswith('public_'):
            return True
        
        # User-specific indices
        if index.startswith(f'user_{user_id}_'):
            return True
        
        # Admin indices
        if index.startswith('admin_'):
            return await self.is_admin_user(user_id)
        
        return False
    
    async def _can_access_redis_key(self, user_id: int, key: str) -> bool:
        """Check if user can access Redis key."""
        
        # Public keys
        if key.startswith('public:'):
            return True
        
        # User-specific keys
        if key.startswith(f'user:{user_id}:'):
            return True
        
        # Session keys
        if key.startswith('session:') and f':{user_id}:' in key:
            return True
        
        return False
    
    def _extract_postgres_tables(self, parsed_query) -> Set[str]:
        """Extract table names from parsed PostgreSQL query."""
        
        tables = set()
        
        def extract_from_token(token):
            if token.ttype is None and isinstance(token, sqlparse.sql.IdentifierList):
                for identifier in token.get_identifiers():
                    tables.add(identifier.get_name())
            elif token.ttype is None and isinstance(token, sqlparse.sql.Identifier):
                tables.add(token.get_name())
        
        # Walk through tokens to find table names
        for token in parsed_query.flatten():
            if token.ttype is sqlparse.tokens.Name:
                # Simple heuristic: if it's after FROM or JOIN, it's likely a table
                tables.add(token.value)
        
        return tables
    
    def _has_where_clause(self, parsed_query) -> bool:
        """Check if query has WHERE clause."""
        
        query_str = str(parsed_query).upper()
        return 'WHERE' in query_str
    
    def _contains_dangerous_sql_functions(self, query: str) -> bool:
        """Check for dangerous SQL functions."""
        
        query_lower = query.lower()
        return any(func in query_lower for func in self.dangerous_sql_functions) 