"""
Example service demonstrating OpenTelemetry custom instrumentation
"""

import time
import logging
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from opentelemetry import trace, metrics
from opentelemetry.trace import Status, StatusCode
from app.core.telemetry import get_tracer, get_meter

logger = logging.getLogger(__name__)

# Get tracer and meter instances
tracer = get_tracer()
meter = get_meter()

# Create custom metrics
request_counter = meter.create_counter(
    name="backend_requests_total",
    description="Total number of requests processed",
    unit="requests"
)

request_duration = meter.create_histogram(
    name="backend_request_duration_seconds",
    description="Request processing duration",
    unit="seconds"
)

database_operations = meter.create_counter(
    name="backend_database_operations_total",
    description="Total database operations",
    unit="operations"
)

llm_requests = meter.create_counter(
    name="backend_llm_requests_total",
    description="Total LLM requests made",
    unit="requests"
)


class TelemetryService:
    """Service demonstrating OpenTelemetry usage patterns."""
    
    def __init__(self):
        self.tracer = tracer
        self.meter = meter
    
    @asynccontextmanager
    async def trace_operation(self, operation_name: str, **attributes):
        """Context manager for tracing operations."""
        with self.tracer.start_as_current_span(operation_name) as span:
            start_time = time.time()
            try:
                # Add custom attributes
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
                
                yield span
                
                # Mark as successful
                span.set_status(Status(StatusCode.OK))
                
            except Exception as e:
                # Record exception and mark as error
                span.record_exception(e)
                span.set_status(Status(StatusCode.ERROR, str(e)))
                raise
            finally:
                # Record metrics
                duration = time.time() - start_time
                request_duration.record(duration, {
                    "operation": operation_name,
                    "status": "success" if span.status.status_code == StatusCode.OK else "error"
                })
    
    async def process_user_request(self, user_id: str, request_type: str) -> Dict[str, Any]:
        """Example: Process a user request with tracing."""
        async with self.trace_operation(
            "process_user_request",
            user_id=user_id,
            request_type=request_type
        ) as span:
            # Increment request counter
            request_counter.add(1, {
                "request_type": request_type,
                "user_id": user_id
            })
            
            # Simulate processing steps
            result = await self._validate_request(user_id, request_type)
            result.update(await self._fetch_user_data(user_id))
            result.update(await self._process_business_logic(result))
            
            span.add_event("Request processed successfully", {
                "result_size": len(str(result))
            })
            
            return result
    
    async def _validate_request(self, user_id: str, request_type: str) -> Dict[str, Any]:
        """Example: Validate request with nested span."""
        with self.tracer.start_as_current_span("validate_request") as span:
            span.set_attributes({
                "user_id": user_id,
                "request_type": request_type
            })
            
            # Simulate validation logic
            await self._simulate_async_work(0.1)
            
            if not user_id:
                span.add_event("Validation failed: missing user_id")
                raise ValueError("User ID is required")
            
            span.add_event("Validation successful")
            return {"validation": "passed", "user_id": user_id}
    
    async def _fetch_user_data(self, user_id: str) -> Dict[str, Any]:
        """Example: Database operation with tracing."""
        with self.tracer.start_as_current_span("fetch_user_data") as span:
            span.set_attributes({
                "user_id": user_id,
                "database.operation": "SELECT",
                "database.table": "users"
            })
            
            # Increment database operation counter
            database_operations.add(1, {
                "operation": "SELECT",
                "table": "users"
            })
            
            # Simulate database query
            await self._simulate_async_work(0.2)
            
            user_data = {
                "user_id": user_id,
                "name": f"User {user_id}",
                "preferences": {"theme": "dark", "language": "en"}
            }
            
            span.add_event("User data fetched", {
                "record_count": 1
            })
            
            return {"user_data": user_data}
    
    async def _process_business_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Example: Business logic with multiple operations."""
        with self.tracer.start_as_current_span("process_business_logic") as span:
            span.set_attributes({
                "data_keys": ",".join(data.keys())
            })
            
            # Simulate multiple processing steps
            results = []
            
            # Step 1: Data processing
            with self.tracer.start_as_current_span("data_processing"):
                await self._simulate_async_work(0.15)
                results.append("data_processed")
            
            # Step 2: LLM call (if needed)
            if data.get("needs_llm", False):
                llm_result = await self._call_llm_service(data)
                results.append(llm_result)
            
            # Step 3: Cache update
            with self.tracer.start_as_current_span("cache_update"):
                await self._simulate_async_work(0.05)
                results.append("cache_updated")
            
            span.add_event("Business logic completed", {
                "steps_completed": len(results)
            })
            
            return {"processing_results": results}
    
    async def _call_llm_service(self, data: Dict[str, Any]) -> str:
        """Example: External service call with tracing."""
        with self.tracer.start_as_current_span("llm_service_call") as span:
            span.set_attributes({
                "service.name": "brain_net_llm",
                "llm.model": "gpt-3.5-turbo",
                "llm.prompt_length": len(str(data))
            })
            
            # Increment LLM request counter
            llm_requests.add(1, {
                "model": "gpt-3.5-turbo"
            })
            
            try:
                # Simulate LLM API call
                await self._simulate_async_work(1.0)  # LLM calls are typically slower
                
                result = "LLM response generated"
                span.set_attributes({
                    "llm.response_length": len(result),
                    "llm.tokens_used": 150
                })
                
                span.add_event("LLM call successful")
                return result
                
            except Exception as e:
                span.add_event("LLM call failed", {"error": str(e)})
                raise
    
    async def _simulate_async_work(self, duration: float):
        """Simulate async work for demo purposes."""
        import asyncio
        await asyncio.sleep(duration)
    
    def record_custom_metric(self, metric_name: str, value: float, attributes: Optional[Dict[str, str]] = None):
        """Record a custom metric."""
        # This would typically be done with pre-created meter instruments
        # This is just for demonstration
        if attributes is None:
            attributes = {}
        
        logger.info(f"Recording custom metric: {metric_name}={value}, attributes={attributes}")


# Global service instance
telemetry_service = TelemetryService() 