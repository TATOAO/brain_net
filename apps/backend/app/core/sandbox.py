"""
Python Sandbox Environment for AI Agents
Provides secure code execution with database access and debugging capabilities.
"""

import asyncio
import sys
import io
import traceback
import inspect
import time
import resource
import signal
import ast
import types
import builtins
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from typing import Dict, Any, Optional, List, Callable, AsyncGenerator, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import pickle
import tempfile
import os
import uuid
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


class SandboxStatus(str, Enum):
    """Status of sandbox execution."""
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class ExecutionResult(BaseModel):
    """Result of code execution in sandbox."""
    execution_id: str
    status: SandboxStatus
    result: Any = None
    stdout: str = ""
    stderr: str = ""
    error: Optional[str] = None
    execution_time: float = 0.0
    memory_usage: Optional[int] = None
    debug_info: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


@dataclass
class SandboxConfig:
    """Configuration for sandbox environment."""
    max_execution_time: int = 30  # seconds
    max_memory_mb: int = 256  # MB
    max_output_size: int = 1024 * 1024  # 1MB
    enable_file_access: bool = False
    enable_network_access: bool = False
    allowed_modules: List[str] = field(default_factory=lambda: [
        'json', 'datetime', 'math', 'random', 'collections', 'itertools',
        'functools', 'operator', 're', 'string', 'uuid', 'hashlib',
        'base64', 'urllib.parse', 'typing', 'dataclasses', 'enum',
        'asyncio', 'pandas', 'numpy', 'requests', 'aiohttp'
    ])
    blocked_modules: List[str] = field(default_factory=lambda: [
        'os', 'sys', 'subprocess', 'importlib', 'builtins.__import__',
        'eval', 'exec', 'compile', 'open', 'input', 'raw_input',
        'file', 'reload', 'vars', 'dir', 'globals', 'locals',
        'socket', 'urllib', 'http', 'ftplib', 'smtplib', 'telnetlib'
    ])
    enable_debugging: bool = True
    save_intermediate_results: bool = True


class DatabaseAccessLayer:
    """Secure database access layer for sandbox."""
    
    def __init__(self, db_session: AsyncSession, user_id: int):
        self.db_session = db_session
        self.user_id = user_id
        self.query_log: List[Dict[str, Any]] = []
    
    async def execute_query(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Execute a SQL query with logging and validation."""
        try:
            # Log the query
            query_info = {
                'query': query,
                'parameters': parameters or {},
                'timestamp': datetime.utcnow(),
                'user_id': self.user_id
            }
            self.query_log.append(query_info)
            
            # Validate query (basic security)
            if not self._validate_query(query):
                raise ValueError("Query validation failed: potentially dangerous operation")
            
            # Execute query
            result = await self.db_session.execute(text(query), parameters or {})
            
            # Convert to dict format
            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            else:
                return [{"affected_rows": result.rowcount}]
                
        except Exception as e:
            logger.error(f"Database query error: {e}")
            raise
    
    def _validate_query(self, query: str) -> bool:
        """Validate SQL query for security."""
        query_lower = query.lower().strip()
        
        # Block dangerous operations
        dangerous_patterns = [
            'drop table', 'drop database', 'drop schema', 'truncate table',
            'delete from', 'update.*set', 'alter table', 'create table',
            'grant', 'revoke', 'shutdown', 'exec', 'execute'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in query_lower:
                return False
        
        return True
    
    async def get_tables(self) -> List[str]:
        """Get list of available tables."""
        query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """
        result = await self.execute_query(query)
        return [row['table_name'] for row in result]
    
    async def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get schema for a specific table."""
        query = """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = :table_name
            ORDER BY ordinal_position
        """
        return await self.execute_query(query, {'table_name': table_name})


class SandboxDebugger:
    """Debugging utilities for sandbox environment."""
    
    def __init__(self):
        self.debug_log: List[Dict[str, Any]] = []
        self.breakpoints: List[int] = []
        self.variable_history: Dict[str, List[Any]] = {}
    
    def log(self, message: str, level: str = "INFO", data: Any = None):
        """Log debug message."""
        entry = {
            'timestamp': datetime.utcnow(),
            'level': level,
            'message': message,
            'data': data,
            'frame_info': self._get_frame_info()
        }
        self.debug_log.append(entry)
        logger.log(getattr(logging, level), f"[SANDBOX] {message}")
    
    def _get_frame_info(self) -> Dict[str, Any]:
        """Get current frame information."""
        frame = inspect.currentframe()
        if frame and frame.f_back:
            frame = frame.f_back.f_back  # Go back to caller
            return {
                'filename': frame.f_code.co_filename,
                'function': frame.f_code.co_name,
                'line_number': frame.f_lineno,
                'locals': {k: str(v) for k, v in frame.f_locals.items() if not k.startswith('_')}
            }
        return {}
    
    def inspect_variable(self, name: str, value: Any):
        """Inspect a variable and track its history."""
        if name not in self.variable_history:
            self.variable_history[name] = []
        
        var_info = {
            'timestamp': datetime.utcnow(),
            'value': value,
            'type': type(value).__name__,
            'size': sys.getsizeof(value) if hasattr(sys, 'getsizeof') else 0,
            'repr': repr(value)[:1000]  # Limit representation size
        }
        self.variable_history[name].append(var_info)
        
        self.log(f"Variable '{name}' = {repr(value)[:200]}", "DEBUG")
    
    def get_debug_summary(self) -> Dict[str, Any]:
        """Get summary of debug information."""
        return {
            'total_logs': len(self.debug_log),
            'log_levels': {level: len([l for l in self.debug_log if l['level'] == level]) 
                          for level in ['DEBUG', 'INFO', 'WARNING', 'ERROR']},
            'tracked_variables': len(self.variable_history),
            'variable_names': list(self.variable_history.keys()),
            'recent_logs': self.debug_log[-10:] if self.debug_log else []
        }


class PythonSandbox:
    """Main sandbox environment for secure Python code execution."""
    
    def __init__(self, config: SandboxConfig = None, db_session: AsyncSession = None, user_id: int = None):
        self.config = config or SandboxConfig()
        self.db_session = db_session
        self.user_id = user_id
        self.execution_id = str(uuid.uuid4())
        self.status = SandboxStatus.CREATED
        self.debugger = SandboxDebugger() if self.config.enable_debugging else None
        self.db_access = DatabaseAccessLayer(db_session, user_id) if db_session and user_id else None
        
        # Execution state
        self.globals_dict = {}
        self.locals_dict = {}
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()
        self.start_time = None
        self.end_time = None
        
        # Resource tracking
        self.memory_usage = 0
        self.cpu_time = 0
        
        # Setup restricted environment
        self._setup_restricted_environment()
    
    def _setup_restricted_environment(self):
        """Setup restricted Python environment."""
        # Create restricted globals
        restricted_builtins = {
            'len': builtins.len,
            'str': builtins.str,
            'int': builtins.int,
            'float': builtins.float,
            'bool': builtins.bool,
            'list': builtins.list,
            'dict': builtins.dict,
            'tuple': builtins.tuple,
            'set': builtins.set,
            'frozenset': builtins.frozenset,
            'range': builtins.range,
            'enumerate': builtins.enumerate,
            'zip': builtins.zip,
            'map': builtins.map,
            'filter': builtins.filter,
            'sorted': builtins.sorted,
            'reversed': builtins.reversed,
            'min': builtins.min,
            'max': builtins.max,
            'sum': builtins.sum,
            'abs': builtins.abs,
            'round': builtins.round,
            'pow': builtins.pow,
            'isinstance': builtins.isinstance,
            'issubclass': builtins.issubclass,
            'hasattr': builtins.hasattr,
            'getattr': builtins.getattr,
            'setattr': builtins.setattr,
            'print': self._safe_print,
            'type': builtins.type,
            'repr': builtins.repr,
            'chr': builtins.chr,
            'ord': builtins.ord,
            'hex': builtins.hex,
            'oct': builtins.oct,
            'bin': builtins.bin,
            'any': builtins.any,
            'all': builtins.all,
        }
        
        # Add debugging utilities if enabled
        if self.config.enable_debugging:
            restricted_builtins.update({
                'debug': self.debugger.log,
                'inspect_var': self.debugger.inspect_variable,
                'get_debug_info': self.debugger.get_debug_summary,
            })
        
        # Add database access if available
        if self.db_access:
            restricted_builtins.update({
                'db_query': self.db_access.execute_query,
                'db_tables': self.db_access.get_tables,
                'db_schema': self.db_access.get_table_schema,
            })
        
        self.globals_dict = {
            '__builtins__': restricted_builtins,
            '__name__': '__sandbox__',
            '__doc__': 'Sandbox execution environment',
        }
    
    def _safe_print(self, *args, **kwargs):
        """Safe print function that writes to buffer."""
        print(*args, **kwargs, file=self.stdout_buffer)
    
    def _validate_code(self, code: str) -> bool:
        """Validate code for security issues."""
        try:
            # Parse code into AST
            tree = ast.parse(code)
            
            # Check for dangerous operations
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.config.blocked_modules:
                            raise ValueError(f"Import of '{alias.name}' is not allowed")
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.config.blocked_modules:
                        raise ValueError(f"Import from '{node.module}' is not allowed")
                
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['eval', 'exec', 'compile', '__import__']:
                            raise ValueError(f"Call to '{node.func.id}' is not allowed")
            
            return True
            
        except SyntaxError as e:
            raise ValueError(f"Syntax error in code: {e}")
        except Exception as e:
            raise ValueError(f"Code validation failed: {e}")
    
    @contextmanager
    def _timeout_context(self):
        """Context manager for execution timeout."""
        def timeout_handler(signum, frame):
            raise TimeoutError("Execution timeout")
        
        if sys.platform != "win32":  # Unix-like systems
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(self.config.max_execution_time)
            try:
                yield
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)
        else:
            # Windows doesn't support SIGALRM, use a different approach
            yield
    
    async def execute_code(self, code: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """Execute Python code in sandbox environment."""
        self.start_time = time.time()
        self.status = SandboxStatus.RUNNING
        
        try:
            # Validate code
            self._validate_code(code)
            
            # Add context to globals
            if context:
                self.globals_dict.update(context)
            
            # Setup resource limits
            if hasattr(resource, 'setrlimit'):
                # Memory limit
                resource.setrlimit(resource.RLIMIT_AS, (
                    self.config.max_memory_mb * 1024 * 1024,
                    self.config.max_memory_mb * 1024 * 1024
                ))
                
                # CPU time limit
                resource.setrlimit(resource.RLIMIT_CPU, (
                    self.config.max_execution_time,
                    self.config.max_execution_time
                ))
            
            # Execute code with timeout
            with self._timeout_context():
                with redirect_stdout(self.stdout_buffer), redirect_stderr(self.stderr_buffer):
                    if self.debugger:
                        self.debugger.log("Starting code execution", "INFO")
                    
                    # Execute the code
                    exec(code, self.globals_dict, self.locals_dict)
                    
                    # Get result (if any)
                    result = self.locals_dict.get('__result__', None)
                    
                    if self.debugger:
                        self.debugger.log("Code execution completed", "INFO")
            
            self.end_time = time.time()
            self.status = SandboxStatus.COMPLETED
            
            return ExecutionResult(
                execution_id=self.execution_id,
                status=self.status,
                result=result,
                stdout=self.stdout_buffer.getvalue(),
                stderr=self.stderr_buffer.getvalue(),
                execution_time=self.end_time - self.start_time,
                debug_info=self.debugger.get_debug_summary() if self.debugger else {},
                completed_at=datetime.utcnow()
            )
            
        except TimeoutError:
            self.status = SandboxStatus.TIMEOUT
            error_msg = f"Execution timeout after {self.config.max_execution_time} seconds"
            
        except MemoryError:
            self.status = SandboxStatus.FAILED
            error_msg = f"Memory limit exceeded ({self.config.max_memory_mb} MB)"
            
        except Exception as e:
            self.status = SandboxStatus.FAILED
            error_msg = f"Execution error: {str(e)}"
            
            if self.debugger:
                self.debugger.log(f"Execution failed: {error_msg}", "ERROR", {
                    'exception_type': type(e).__name__,
                    'traceback': traceback.format_exc()
                })
        
        self.end_time = time.time()
        
        return ExecutionResult(
            execution_id=self.execution_id,
            status=self.status,
            error=error_msg,
            stdout=self.stdout_buffer.getvalue(),
            stderr=self.stderr_buffer.getvalue(),
            execution_time=self.end_time - self.start_time if self.start_time else 0,
            debug_info=self.debugger.get_debug_summary() if self.debugger else {},
            completed_at=datetime.utcnow()
        )
    
    async def execute_interactive(self, code: str, context: Dict[str, Any] = None) -> AsyncGenerator[str, None]:
        """Execute code interactively, yielding output as it's generated."""
        # This would be implemented for interactive debugging
        # For now, just execute and return result
        result = await self.execute_code(code, context)
        yield f"Output: {result.stdout}"
        if result.stderr:
            yield f"Error: {result.stderr}"
        if result.result:
            yield f"Result: {result.result}"
    
    def get_execution_state(self) -> Dict[str, Any]:
        """Get current execution state."""
        return {
            'execution_id': self.execution_id,
            'status': self.status,
            'variables': {k: repr(v)[:100] for k, v in self.locals_dict.items() if not k.startswith('_')},
            'globals': list(self.globals_dict.keys()),
            'debug_info': self.debugger.get_debug_summary() if self.debugger else None,
            'query_log': self.db_access.query_log if self.db_access else [],
            'execution_time': (time.time() - self.start_time) if self.start_time else 0
        }
    
    def cleanup(self):
        """Clean up sandbox resources."""
        if self.debugger:
            self.debugger.log("Cleaning up sandbox", "INFO")
        
        # Clear buffers
        self.stdout_buffer.close()
        self.stderr_buffer.close()
        
        # Clear execution state
        self.globals_dict.clear()
        self.locals_dict.clear()


class SandboxManager:
    """Manager for multiple sandbox instances."""
    
    def __init__(self, db_session_factory: sessionmaker):
        self.db_session_factory = db_session_factory
        self.active_sandboxes: Dict[str, PythonSandbox] = {}
        self.execution_history: List[ExecutionResult] = []
    
    async def create_sandbox(self, user_id: int, config: SandboxConfig = None) -> str:
        """Create a new sandbox instance."""
        db_session = self.db_session_factory()
        sandbox = PythonSandbox(config, db_session, user_id)
        
        self.active_sandboxes[sandbox.execution_id] = sandbox
        return sandbox.execution_id
    
    async def execute_in_sandbox(self, sandbox_id: str, code: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """Execute code in a specific sandbox."""
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found")
        
        sandbox = self.active_sandboxes[sandbox_id]
        result = await sandbox.execute_code(code, context)
        
        # Store result in history
        self.execution_history.append(result)
        
        return result
    
    async def get_sandbox_state(self, sandbox_id: str) -> Dict[str, Any]:
        """Get state of a specific sandbox."""
        if sandbox_id not in self.active_sandboxes:
            raise ValueError(f"Sandbox {sandbox_id} not found")
        
        return self.active_sandboxes[sandbox_id].get_execution_state()
    
    async def cleanup_sandbox(self, sandbox_id: str):
        """Clean up a specific sandbox."""
        if sandbox_id in self.active_sandboxes:
            self.active_sandboxes[sandbox_id].cleanup()
            del self.active_sandboxes[sandbox_id]
    
    async def cleanup_all(self):
        """Clean up all active sandboxes."""
        for sandbox_id in list(self.active_sandboxes.keys()):
            await self.cleanup_sandbox(sandbox_id)
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """Get execution history."""
        return self.execution_history[-limit:] 