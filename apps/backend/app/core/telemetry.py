"""
OpenTelemetry configuration for Brain_Net Backend Service
"""

import os
import logging
from typing import Optional

from opentelemetry import trace, metrics
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Instrumentation
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_resource() -> Resource:
    """Create OpenTelemetry resource with service information."""
    return Resource.create({
        "service.name": "brain_net_backend",
        "service.version": "1.0.0",
        "service.namespace": "brain_net",
        "service.instance.id": os.getenv("HOSTNAME", "unknown"),
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })


def setup_tracing(
    otlp_endpoint: Optional[str] = None,
    insecure: bool = True
) -> None:
    """Setup OpenTelemetry tracing."""
    if not otlp_endpoint:
        # Try to connect to otel-collector first, fallback to Jaeger directly
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
    
    logger.info(f"Setting up tracing with endpoint: {otlp_endpoint}")
    
    # Create resource
    resource = get_resource()
    
    # Setup tracer provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    
    # Setup OTLP exporter
    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=insecure,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)
    
    logger.info("Tracing setup completed")


def setup_metrics(
    otlp_endpoint: Optional[str] = None,
    insecure: bool = True
) -> None:
    """Setup OpenTelemetry metrics."""
    if not otlp_endpoint:
        # Try to connect to otel-collector first, fallback to Jaeger directly
        otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://jaeger:4317")
    
    logger.info(f"Setting up metrics with endpoint: {otlp_endpoint}")
    
    # Create resource
    resource = get_resource()
    
    # Setup metric exporter
    metric_exporter = OTLPMetricExporter(
        endpoint=otlp_endpoint,
        insecure=insecure,
    )
    
    # Setup metric reader
    metric_reader = PeriodicExportingMetricReader(
        exporter=metric_exporter,
        export_interval_millis=30000,  # 30 seconds
        export_timeout_millis=30000,
    )
    
    # Setup meter provider
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[metric_reader]
    )
    metrics.set_meter_provider(meter_provider)
    
    logger.info("Metrics setup completed")


def setup_instrumentation(app=None) -> None:
    """Setup automatic instrumentation for common libraries."""
    logger.info("Setting up automatic instrumentation...")
    
    try:
        # FastAPI instrumentation - requires app instance
        if app is not None:
            FastAPIInstrumentor.instrument_app(app)
        
        # Database instrumentation
        try:
            SQLAlchemyInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"SQLAlchemy instrumentation failed: {e}")
        
        try:
            AsyncPGInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"AsyncPG instrumentation failed: {e}")
        
        # Cache instrumentation
        try:
            RedisInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"Redis instrumentation failed: {e}")
        
        # HTTP client instrumentation
        try:
            HTTPXClientInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"HTTPX instrumentation failed: {e}")
            
        try:
            RequestsInstrumentor().instrument()
        except Exception as e:
            logger.warning(f"Requests instrumentation failed: {e}")
        
        # Logging instrumentation
        try:
            LoggingInstrumentor().instrument(set_logging_format=True)
        except Exception as e:
            logger.warning(f"Logging instrumentation failed: {e}")
        
        logger.info("Automatic instrumentation setup completed")
        
    except Exception as e:
        logger.error(f"Failed to setup instrumentation: {e}")
        raise


def initialize_telemetry(app=None) -> None:
    """Initialize OpenTelemetry for the backend service."""
    if not settings.OTEL_ENABLED:
        logger.info("OpenTelemetry is disabled")
        return
    
    logger.info("Initializing OpenTelemetry for Brain_Net Backend...")
    
    try:
        # Setup tracing and metrics
        setup_tracing()
        setup_metrics()
        
        # Setup automatic instrumentation
        setup_instrumentation(app)
        
        logger.info("OpenTelemetry initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize OpenTelemetry: {e}")
        if settings.OTEL_REQUIRED:
            raise
        else:
            logger.warning("Continuing without OpenTelemetry")


def get_tracer(name: str = "brain_net_backend"):
    """Get a tracer instance."""
    return trace.get_tracer(name)


def get_meter(name: str = "brain_net_backend"):
    """Get a meter instance."""
    return metrics.get_meter(name) 