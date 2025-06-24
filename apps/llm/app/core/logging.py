"""
Logging configuration for Brain_Net LLM Service
"""

import logging
import sys
from typing import Dict, Any
import structlog
from app.core.config import settings


def setup_logging() -> None:
    """Configure structured logging for the LLM service."""
    
    # Configure standard logging
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/llm_service.log", mode="a")
        ]
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance."""
    return structlog.get_logger(name)


class LLMLogger:
    """Specialized logger for LLM operations."""
    
    def __init__(self, component: str):
        self.logger = get_logger(f"llm.{component}")
    
    def log_model_load(self, model_name: str, load_time: float) -> None:
        """Log model loading event."""
        self.logger.info(
            "model_loaded",
            model_name=model_name,
            load_time_seconds=load_time
        )
    
    def log_inference(self, model_name: str, input_tokens: int, output_tokens: int, 
                     response_time: float, user_id: str = None) -> None:
        """Log inference event."""
        self.logger.info(
            "inference_completed",
            model_name=model_name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            response_time_seconds=response_time,
            user_id=user_id
        )
    
    def log_rag_query(self, query: str, documents_retrieved: int, 
                     similarity_scores: list, response_time: float) -> None:
        """Log RAG query event."""
        self.logger.info(
            "rag_query_processed",
            query_length=len(query),
            documents_retrieved=documents_retrieved,
            avg_similarity_score=sum(similarity_scores) / len(similarity_scores) if similarity_scores else 0,
            response_time_seconds=response_time
        )
    
    def log_agent_execution(self, agent_type: str, task: str, steps: int, 
                           success: bool, execution_time: float) -> None:
        """Log agent execution event."""
        self.logger.info(
            "agent_execution_completed",
            agent_type=agent_type,
            task_description=task[:100],  # Truncate long tasks
            steps_executed=steps,
            success=success,
            execution_time_seconds=execution_time
        )
    
    def log_error(self, error_type: str, error_message: str, 
                 additional_context: Dict[str, Any] = None) -> None:
        """Log error event."""
        context = additional_context or {}
        self.logger.error(
            "error_occurred",
            error_type=error_type,
            error_message=error_message,
            **context
        ) 