"""
Structured logging system for WeQuo with JSON formatting and performance tracking.
"""

import json
import logging
import time
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union
from functools import wraps
from dataclasses import dataclass, asdict


@dataclass
class LogContext:
    """Context information for structured logging."""
    operation: str
    component: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    connector_name: Optional[str] = None
    data_source: Optional[str] = None
    record_count: Optional[int] = None
    duration_ms: Optional[float] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "thread": record.thread,
            "process": record.process
        }
        
        # Add context if available
        if hasattr(record, 'context') and record.context:
            log_entry.update(asdict(record.context))
        
        # Add exception info if available
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'getMessage', 'exc_info', 
                          'exc_text', 'stack_info', 'context']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str)


class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.timers = {}
    
    def start_timer(self, operation: str, context: Optional[LogContext] = None):
        """Start timing an operation."""
        self.timers[operation] = {
            'start_time': time.time(),
            'context': context
        }
    
    def end_timer(self, operation: str, success: bool = True, error_message: Optional[str] = None):
        """End timing an operation and log the result."""
        if operation not in self.timers:
            self.logger.warning(f"Timer for operation '{operation}' was not started")
            return
        
        timer_data = self.timers.pop(operation)
        duration_ms = (time.time() - timer_data['start_time']) * 1000
        
        context = timer_data['context']
        if context:
            context.duration_ms = duration_ms
            if not success and error_message:
                context.error_message = error_message
        
        # Log performance metrics
        self.logger.info(
            f"Operation '{operation}' completed",
            extra={
                'context': context,
                'performance': {
                    'operation': operation,
                    'duration_ms': duration_ms,
                    'success': success,
                    'error_message': error_message
                }
            }
        )
    
    def log_metrics(self, metrics: Dict[str, Any], context: Optional[LogContext] = None):
        """Log performance metrics."""
        self.logger.info(
            "Performance metrics recorded",
            extra={
                'context': context,
                'metrics': metrics
            }
        )


class WeQuoLogger:
    """Main logger class for WeQuo system."""
    
    def __init__(self, name: str, log_level: str = "INFO", log_file: Optional[Union[str, Path]] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with structured formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_path)
            file_handler.setFormatter(StructuredFormatter())
            self.logger.addHandler(file_handler)
        
        # Performance logger
        self.performance = PerformanceLogger(self.logger)
    
    def info(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log info message with context."""
        self.logger.info(message, extra={'context': context, **kwargs})
    
    def warning(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log warning message with context."""
        self.logger.warning(message, extra={'context': context, **kwargs})
    
    def error(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log error message with context."""
        self.logger.error(message, extra={'context': context, **kwargs})
    
    def debug(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log debug message with context."""
        self.logger.debug(message, extra={'context': context, **kwargs})
    
    def critical(self, message: str, context: Optional[LogContext] = None, **kwargs):
        """Log critical message with context."""
        self.logger.critical(message, extra={'context': context, **kwargs})


def log_operation(operation: str, component: str = "unknown"):
    """Decorator to automatically log operation start/end with timing."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create logger for this operation
            logger = WeQuoLogger(f"{component}.{operation}")
            
            # Create context
            context = LogContext(
                operation=operation,
                component=component,
                pipeline_run_id=kwargs.get('pipeline_run_id'),
                connector_name=kwargs.get('connector_name'),
                data_source=kwargs.get('data_source')
            )
            
            # Start timing
            logger.performance.start_timer(operation, context)
            
            try:
                logger.info(f"Starting {operation}", context=context)
                result = func(*args, **kwargs)
                
                # Log success
                if hasattr(result, '__len__') and not isinstance(result, str):
                    context.record_count = len(result)
                
                logger.performance.end_timer(operation, success=True)
                logger.info(f"Completed {operation}", context=context)
                
                return result
                
            except Exception as e:
                # Log error
                context.error_message = str(e)
                context.error_code = type(e).__name__
                
                logger.performance.end_timer(operation, success=False, error_message=str(e))
                logger.error(f"Failed {operation}: {e}", context=context)
                
                raise
        
        return wrapper
    return decorator


def setup_wequo_logging(
    log_level: str = "INFO",
    log_file: Optional[Union[str, Path]] = None,
    component: str = "wequo"
) -> WeQuoLogger:
    """Setup WeQuo logging system."""
    return WeQuoLogger(component, log_level, log_file)


# Global logger instances
def get_logger(name: str) -> WeQuoLogger:
    """Get a logger instance for a specific component."""
    return WeQuoLogger(name)


# Component-specific loggers
connector_logger = get_logger("wequo.connectors")
analytics_logger = get_logger("wequo.analytics")
monitoring_logger = get_logger("wequo.monitoring")
pipeline_logger = get_logger("wequo.pipeline")
