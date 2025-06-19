"""
Logging configuration for Brain_Net Backend
Provides structured logging with JSON format support.
"""

import logging
import logging.config
import sys
from typing import Dict, Any
import json
from datetime import datetime
import os

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output in development."""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors."""
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']
        
        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')
        
        # Format the message
        formatted_message = (
            f"{color}[{timestamp}] {record.levelname:8} "
            f"{record.name}:{record.lineno} - {record.getMessage()}{reset}"
        )
        
        # Add exception info if present
        if record.exc_info:
            formatted_message += f"\n{self.formatException(record.exc_info)}"
        
        return formatted_message


def setup_logging() -> None:
    """Setup logging configuration based on settings."""
    
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    # Determine log level
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Choose formatter based on format setting and environment
    if settings.LOG_FORMAT.lower() == "json" and not settings.is_development:
        formatter_class = JSONFormatter
        format_string = None
    else:
        formatter_class = ColoredFormatter if settings.is_development else logging.Formatter
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Define handlers based on environment
    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": sys.stdout,
        }
    }
    
    # Add file handler if not in development or if explicitly enabled
    if not settings.is_development or os.getenv("ENABLE_FILE_LOGGING", "false").lower() == "true":
        handlers["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": "logs/brain_net.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        }
    
    # Determine which handlers to use
    handler_names = ["console"]
    if "file" in handlers:
        handler_names.append("file")
    
    # Logging configuration
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "()": formatter_class,
                "format": format_string,
            }
        },
        "handlers": handlers,
        "loggers": {
            "": {  # Root logger
                "level": log_level,
                "handlers": handler_names,
                "propagate": False,
            },
            "uvicorn": {
                "level": log_level,
                "handlers": handler_names,
                "propagate": False,
            },
            "uvicorn.access": {
                "level": log_level,
                "handlers": handler_names,
                "propagate": False,
            },
            "sqlalchemy": {
                "level": logging.WARNING if not settings.DEBUG_SQL else logging.INFO,
                "handlers": handler_names,
                "propagate": False,
            },
            "elasticsearch": {
                "level": logging.WARNING if not settings.DEBUG_ELASTICSEARCH else logging.INFO,
                "handlers": handler_names,
                "propagate": False,
            }
        }
    }
    
    # Apply logging configuration
    logging.config.dictConfig(logging_config)
    
    # Set up specific logger levels for third-party libraries
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("neo4j").setLevel(logging.WARNING)
    logging.getLogger("minio").setLevel(logging.WARNING)
    
    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(name)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class."""
    
    @property
    def logger(self) -> logging.Logger:
        """Get logger instance for this class."""
        return logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    def log_extra(self, level: int, message: str, **extra_fields) -> None:
        """Log message with extra fields."""
        logger = self.logger
        if logger.isEnabledFor(level):
            record = logger.makeRecord(
                logger.name, level, "", 0, message, (), None
            )
            record.extra_fields = extra_fields
            logger.handle(record) 