"""
Sandbox Manager for Brain_Net Backend
Manages sandbox instances, resource limits, and security policies.
"""

import asyncio
import psutil
import signal
import time
from typing import Dict, Any, Optional, List, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import logging
import json
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref

from app.core.sandbox import PythonSandbox, SandboxConfig, ExecutionResult, SandboxStatus
from app.core.config import get_settings
from app.core.processors import create_processor_instance, validate_processor_code
from apps.shared.models import UserProcessor, UserPipeline


logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Resource limits for sandbox execution."""
    max_memory_mb: int = 256
    max_cpu_percent: float = 50.0
    max_execution_time: int = 30
    max_open_files: int = 100
    max_processes: int = 5
    max_threads: int = 10


@dataclass
class SecurityPolicy:
    """Security policy for sandbox execution."""
    allowed_modules: Set[str] = field(default_factory=lambda: {
        'json', 'datetime', 'math', 'random', 'collections', 'itertools',
        'functools', 'operator', 're', 'string', 'uuid', 'hashlib',
        'base64', 'urllib.parse', 'typing', 'dataclasses', 'enum',
        'asyncio', 'pandas', 'numpy', 'requests', 'aiohttp'
    })
    blocked_modules: Set[str] = field(default_factory=lambda: {
        'os', 'sys', 'subprocess', 'importlib', 'builtins.__import__',
        'eval', 'exec', 'compile', 'open', 'input', 'raw_input',
        'file', 'reload', 'vars', 'dir', 'globals', 'locals',
        'socket', 'urllib', 'http', 'ftplib', 'smtplib', 'telnetlib'
    })
    blocked_functions: Set[str] = field(default_factory=lambda: {
        'exec', 'eval', 'compile', '__import__', 'getattr', 'setattr',
        'delattr', 'hasattr', 'globals', 'locals', 'vars', 'dir'
    })
    max_code_length: int = 10000
    allow_file_access: bool = False
    allow_network_access: bool = False


@dataclass
class SandboxMetrics:
    """Metrics for sandbox performance monitoring."""
    total_sandboxes_created: int = 0
    active_sandboxes: int = 0
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    timeout_executions: int = 0
    total_execution_time: float = 0.0
    average_execution_time: float = 0.0
    peak_memory_usage: float = 0.0
    peak_cpu_usage: float = 0.0
    
    def update_execution(self, result: ExecutionResult):
        """Update metrics with execution result."""
        self.total_executions += 1
        self.total_execution_time += result.execution_time
        self.average_execution_time = self.total_execution_time / self.total_executions
        
        if result.status == SandboxStatus.COMPLETED:
            self.successful_executions += 1
        elif result.status == SandboxStatus.FAILED:
            self.failed_executions += 1
        elif result.status == SandboxStatus.TIMEOUT:
            self.timeout_executions += 1
        
        if result.memory_usage:
            self.peak_memory_usage = max(self.peak_memory_usage, result.memory_usage)


class SandboxResourceMonitor:
    """Monitor and enforce resource limits for sandboxes."""
    
    def __init__(self, limits: ResourceLimits):
        self.limits = limits
        self.monitored_processes: Dict[str, psutil.Process] = {}
        self.monitoring_active = False
        self.monitor_thread = None
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    def start_monitoring(self):
        """Start resource monitoring thread."""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_resources, daemon=True)
            self.monitor_thread.start()
            logger.info("Sandbox resource monitoring started")
    
    def stop_monitoring(self):
        """Stop resource monitoring thread."""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("Sandbox resource monitoring stopped")
    
    def register_process(self, sandbox_id: str, process: psutil.Process):
        """Register a process for monitoring."""
        self.monitored_processes[sandbox_id] = process
    
    def unregister_process(self, sandbox_id: str):
        """Unregister a process from monitoring."""
        if sandbox_id in self.monitored_processes:
            del self.monitored_processes[sandbox_id]
    
    def _monitor_resources(self):
        """Monitor resources in background thread."""
        while self.monitoring_active:
            try:
                for sandbox_id, process in list(self.monitored_processes.items()):
                    try:
                        if not process.is_running():
                            self.unregister_process(sandbox_id)
                            continue
                        
                        # Check memory usage
                        memory_info = process.memory_info()
                        memory_mb = memory_info.rss / 1024 / 1024
                        
                        if memory_mb > self.limits.max_memory_mb:
                            logger.warning(f"Sandbox {sandbox_id} exceeded memory limit: {memory_mb:.2f}MB")
                            self._terminate_process(sandbox_id, process, "Memory limit exceeded")
                            continue
                        
                        # Check CPU usage
                        cpu_percent = process.cpu_percent()
                        if cpu_percent > self.limits.max_cpu_percent:
                            logger.warning(f"Sandbox {sandbox_id} exceeded CPU limit: {cpu_percent:.2f}%")
                            # Don't terminate immediately for CPU, just log
                        
                        # Check number of open files
                        try:
                            open_files = len(process.open_files())
                            if open_files > self.limits.max_open_files:
                                logger.warning(f"Sandbox {sandbox_id} exceeded open files limit: {open_files}")
                                self._terminate_process(sandbox_id, process, "Open files limit exceeded")
                        except psutil.AccessDenied:
                            pass  # Can't check open files, skip
                        
                        # Check number of threads
                        try:
                            num_threads = process.num_threads()
                            if num_threads > self.limits.max_threads:
                                logger.warning(f"Sandbox {sandbox_id} exceeded thread limit: {num_threads}")
                                self._terminate_process(sandbox_id, process, "Thread limit exceeded")
                        except psutil.AccessDenied:
                            pass  # Can't check threads, skip
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process no longer exists or can't access
                        self.unregister_process(sandbox_id)
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error(f"Error in resource monitoring: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _terminate_process(self, sandbox_id: str, process: psutil.Process, reason: str):
        """Terminate a process that exceeded limits."""
        try:
            logger.error(f"Terminating sandbox {sandbox_id}: {reason}")
            process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=5)
            except psutil.TimeoutExpired:
                # Force kill if not terminated gracefully
                process.kill()
                process.wait(timeout=5)
            
            self.unregister_process(sandbox_id)
            
        except Exception as e:
            logger.error(f"Error terminating process for sandbox {sandbox_id}: {e}")


class EnhancedSandboxManager:
    """Enhanced sandbox manager with resource monitoring and security."""
    
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.settings = get_settings()
        
        # Initialize components
        self.resource_limits = ResourceLimits()
        self.security_policy = SecurityPolicy()
        self.metrics = SandboxMetrics()
        self.resource_monitor = SandboxResourceMonitor(self.resource_limits)
        
        # Sandbox management
        self.active_sandboxes: Dict[str, PythonSandbox] = {}
        self.sandbox_processes: Dict[str, psutil.Process] = {}
        self.execution_history: List[ExecutionResult] = []
        
        # Cleanup management
        self.cleanup_interval = 300  # 5 minutes
        self.max_sandbox_lifetime = 3600  # 1 hour
        self.cleanup_task = None
        
        # Start monitoring
        self.resource_monitor.start_monitoring()
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start periodic cleanup task."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    await self._cleanup_expired_sandboxes()
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
        
        self.cleanup_task = asyncio.create_task(cleanup_loop())
    
    async def _cleanup_expired_sandboxes(self):
        """Clean up expired sandboxes."""
        now = datetime.utcnow()
        expired_sandboxes = []
        
        for sandbox_id, sandbox in self.active_sandboxes.items():
            if hasattr(sandbox, 'created_at'):
                age = (now - sandbox.created_at).total_seconds()
                if age > self.max_sandbox_lifetime:
                    expired_sandboxes.append(sandbox_id)
        
        for sandbox_id in expired_sandboxes:
            logger.info(f"Cleaning up expired sandbox: {sandbox_id}")
            await self.cleanup_sandbox(sandbox_id)
    
    async def create_sandbox(self, user_id: int, config: SandboxConfig = None) -> str:
        """Create a new sandbox with enhanced monitoring."""
        try:
            # Create sandbox config with security policy
            if config is None:
                config = SandboxConfig()
            
            # Apply security policy
            config.allowed_modules = list(self.security_policy.allowed_modules)
            config.blocked_modules = list(self.security_policy.blocked_modules)
            config.max_execution_time = min(config.max_execution_time, self.resource_limits.max_execution_time)
            config.max_memory_mb = min(config.max_memory_mb, self.resource_limits.max_memory_mb)
            
            # Create sandbox
            db_session = self.db_session_factory()
            sandbox = PythonSandbox(config, db_session, user_id)
            sandbox.created_at = datetime.utcnow()
            
            # Register sandbox
            self.active_sandboxes[sandbox.execution_id] = sandbox
            self.metrics.total_sandboxes_created += 1
            self.metrics.active_sandboxes += 1
            
            logger.info(f"Created sandbox {sandbox.execution_id} for user {user_id}")
            
            return sandbox.execution_id
            
        except Exception as e:
            logger.error(f"Failed to create sandbox: {e}")
            raise
    
    async def execute_in_sandbox(self, sandbox_id: str, code: str, context: Dict[str, Any] = None) -> ExecutionResult:
        """Execute code in sandbox with enhanced monitoring."""
        try:
            if sandbox_id not in self.active_sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            sandbox = self.active_sandboxes[sandbox_id]
            
            # Validate code against security policy
            self._validate_code_security(code)
            
            # Get current process for monitoring
            current_process = psutil.Process()
            self.resource_monitor.register_process(sandbox_id, current_process)
            
            # Execute code
            result = await sandbox.execute_code(code, context)
            
            # Update metrics
            self.metrics.update_execution(result)
            
            # Store in history
            self.execution_history.append(result)
            
            # Clean up monitoring
            self.resource_monitor.unregister_process(sandbox_id)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute code in sandbox {sandbox_id}: {e}")
            self.resource_monitor.unregister_process(sandbox_id)
            raise
    
    def _validate_code_security(self, code: str):
        """Validate code against security policy."""
        # Check code length
        if len(code) > self.security_policy.max_code_length:
            raise ValueError(f"Code too long: {len(code)} characters (max: {self.security_policy.max_code_length})")
        
        # Check for blocked functions
        for func in self.security_policy.blocked_functions:
            if func in code:
                raise ValueError(f"Blocked function '{func}' found in code")
        
        # Additional security checks can be added here
        
        # Use existing validation
        validate_processor_code(code)
    
    async def integrate_with_processor(self, sandbox_id: str, processor: UserProcessor) -> ExecutionResult:
        """Integrate sandbox with existing processor system."""
        try:
            if sandbox_id not in self.active_sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            sandbox = self.active_sandboxes[sandbox_id]
            
            # Create processor instance
            processor_instance = create_processor_instance(processor.processor_code, processor.default_config)
            
            # Execute processor in sandbox context
            context = {
                'processor': processor_instance,
                'processor_config': processor.default_config,
                'processor_meta': {
                    'id': processor.id,
                    'name': processor.name,
                    'version': processor.version
                }
            }
            
            # Create execution code
            execution_code = f"""
# Execute processor in sandbox
processor_result = await processor.process(data)
__result__ = processor_result
"""
            
            return await self.execute_in_sandbox(sandbox_id, execution_code, context)
            
        except Exception as e:
            logger.error(f"Failed to integrate sandbox with processor: {e}")
            raise
    
    async def get_sandbox_state(self, sandbox_id: str) -> Dict[str, Any]:
        """Get enhanced sandbox state with resource usage."""
        try:
            if sandbox_id not in self.active_sandboxes:
                raise ValueError(f"Sandbox {sandbox_id} not found")
            
            sandbox = self.active_sandboxes[sandbox_id]
            base_state = sandbox.get_execution_state()
            
            # Add resource usage information
            if sandbox_id in self.sandbox_processes:
                process = self.sandbox_processes[sandbox_id]
                try:
                    memory_info = process.memory_info()
                    base_state['resource_usage'] = {
                        'memory_mb': memory_info.rss / 1024 / 1024,
                        'cpu_percent': process.cpu_percent(),
                        'num_threads': process.num_threads(),
                        'open_files': len(process.open_files())
                    }
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    base_state['resource_usage'] = {'error': 'Unable to get resource usage'}
            
            # Add sandbox metadata
            base_state['sandbox_metadata'] = {
                'created_at': getattr(sandbox, 'created_at', None),
                'lifetime_seconds': (datetime.utcnow() - getattr(sandbox, 'created_at', datetime.utcnow())).total_seconds(),
                'resource_limits': {
                    'max_memory_mb': self.resource_limits.max_memory_mb,
                    'max_cpu_percent': self.resource_limits.max_cpu_percent,
                    'max_execution_time': self.resource_limits.max_execution_time
                }
            }
            
            return base_state
            
        except Exception as e:
            logger.error(f"Failed to get sandbox state: {e}")
            raise
    
    async def cleanup_sandbox(self, sandbox_id: str):
        """Enhanced sandbox cleanup."""
        try:
            if sandbox_id in self.active_sandboxes:
                sandbox = self.active_sandboxes[sandbox_id]
                
                # Clean up sandbox
                sandbox.cleanup()
                
                # Remove from active sandboxes
                del self.active_sandboxes[sandbox_id]
                self.metrics.active_sandboxes -= 1
                
                # Clean up process monitoring
                self.resource_monitor.unregister_process(sandbox_id)
                
                if sandbox_id in self.sandbox_processes:
                    del self.sandbox_processes[sandbox_id]
                
                logger.info(f"Cleaned up sandbox {sandbox_id}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox {sandbox_id}: {e}")
    
    async def cleanup_all(self):
        """Clean up all sandboxes."""
        for sandbox_id in list(self.active_sandboxes.keys()):
            await self.cleanup_sandbox(sandbox_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get sandbox metrics."""
        return {
            'total_sandboxes_created': self.metrics.total_sandboxes_created,
            'active_sandboxes': self.metrics.active_sandboxes,
            'total_executions': self.metrics.total_executions,
            'successful_executions': self.metrics.successful_executions,
            'failed_executions': self.metrics.failed_executions,
            'timeout_executions': self.metrics.timeout_executions,
            'success_rate': (self.metrics.successful_executions / self.metrics.total_executions * 100) if self.metrics.total_executions > 0 else 0,
            'average_execution_time': self.metrics.average_execution_time,
            'peak_memory_usage': self.metrics.peak_memory_usage,
            'peak_cpu_usage': self.metrics.peak_cpu_usage,
            'resource_limits': {
                'max_memory_mb': self.resource_limits.max_memory_mb,
                'max_cpu_percent': self.resource_limits.max_cpu_percent,
                'max_execution_time': self.resource_limits.max_execution_time
            }
        }
    
    def get_execution_history(self, limit: int = 100) -> List[ExecutionResult]:
        """Get execution history with limit."""
        return self.execution_history[-limit:]
    
    def shutdown(self):
        """Shutdown the sandbox manager."""
        # Cancel cleanup task
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        # Stop resource monitoring
        self.resource_monitor.stop_monitoring()
        
        # Clean up all sandboxes
        asyncio.create_task(self.cleanup_all())
        
        logger.info("Sandbox manager shutdown completed")


# Global sandbox manager instance
_sandbox_manager = None


def get_sandbox_manager(db_session_factory) -> EnhancedSandboxManager:
    """Get global sandbox manager instance."""
    global _sandbox_manager
    if _sandbox_manager is None:
        _sandbox_manager = EnhancedSandboxManager(db_session_factory)
    return _sandbox_manager 