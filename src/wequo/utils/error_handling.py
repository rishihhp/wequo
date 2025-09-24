"""
Comprehensive error handling and recovery system for WeQuo.
"""

import logging
import traceback
from typing import Any, Dict, List, Optional, Callable, Type
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    CONNECTION = "connection"
    AUTHENTICATION = "authentication"
    DATA_VALIDATION = "data_validation"
    PROCESSING = "processing"
    STORAGE = "storage"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


@dataclass
class ErrorInfo:
    """Structured error information."""
    error_id: str
    timestamp: str
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    operation: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    recovery_action: Optional[str] = None
    retry_count: int = 0
    resolved: bool = False


class ErrorHandler:
    """Centralized error handling and recovery system."""
    
    def __init__(self, log_file: Optional[Path] = None):
        self.logger = logging.getLogger(__name__)
        self.error_log = []
        self.recovery_strategies = {}
        self.error_patterns = {}
        
        if log_file:
            self.log_file = log_file
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        else:
            self.log_file = Path("logs/error_log.json")
            self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing error log
        self._load_error_log()
        
        # Register default recovery strategies
        self._register_default_strategies()
    
    def _load_error_log(self):
        """Load existing error log from file."""
        try:
            if self.log_file.exists():
                with open(self.log_file, 'r') as f:
                    self.error_log = json.load(f)
        except Exception as e:
            self.logger.warning(f"Could not load error log: {e}")
            self.error_log = []
    
    def _save_error_log(self):
        """Save error log to file."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.error_log, f, indent=2, default=str)
        except Exception as e:
            self.logger.error(f"Could not save error log: {e}")
    
    def _register_default_strategies(self):
        """Register default error recovery strategies."""
        # Connection errors
        self.register_recovery_strategy(
            ErrorCategory.CONNECTION,
            ["ConnectionError", "TimeoutError", "OSError"],
            self._retry_with_backoff
        )
        
        # Authentication errors
        self.register_recovery_strategy(
            ErrorCategory.AUTHENTICATION,
            ["401", "403", "Unauthorized", "Forbidden"],
            self._handle_auth_error
        )
        
        # Data validation errors
        self.register_recovery_strategy(
            ErrorCategory.DATA_VALIDATION,
            ["ValueError", "KeyError", "ValidationError"],
            self._handle_validation_error
        )
        
        # Storage errors
        self.register_recovery_strategy(
            ErrorCategory.STORAGE,
            ["IOError", "OSError", "PermissionError"],
            self._handle_storage_error
        )
    
    def register_recovery_strategy(
        self, 
        category: ErrorCategory, 
        error_patterns: List[str], 
        strategy: Callable
    ):
        """Register a recovery strategy for specific error patterns."""
        self.recovery_strategies[category] = {
            'patterns': error_patterns,
            'strategy': strategy
        }
    
    def handle_error(
        self,
        error: Exception,
        component: str,
        operation: str,
        context: Optional[Dict[str, Any]] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM
    ) -> ErrorInfo:
        """Handle an error and attempt recovery."""
        error_info = self._create_error_info(error, component, operation, context, severity)
        
        # Log the error
        self.logger.error(
            f"Error in {component}.{operation}: {error_info.error_message}",
            extra={'error_info': error_info.__dict__}
        )
        
        # Add to error log
        self.error_log.append(error_info.__dict__)
        
        # Attempt recovery
        recovery_action = self._attempt_recovery(error_info)
        if recovery_action:
            error_info.recovery_action = recovery_action
            self.logger.info(f"Recovery action taken: {recovery_action}")
        
        # Save error log
        self._save_error_log()
        
        return error_info
    
    def _create_error_info(
        self,
        error: Exception,
        component: str,
        operation: str,
        context: Optional[Dict[str, Any]],
        severity: ErrorSeverity
    ) -> ErrorInfo:
        """Create structured error information."""
        import uuid
        from datetime import datetime
        
        error_type = type(error).__name__
        error_message = str(error)
        
        # Classify error category
        category = self._classify_error(error_type, error_message)
        
        # Generate unique error ID
        error_id = str(uuid.uuid4())[:8]
        
        return ErrorInfo(
            error_id=error_id,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            category=category,
            component=component,
            operation=operation,
            error_type=error_type,
            error_message=error_message,
            stack_trace=traceback.format_exc(),
            context=context
        )
    
    def _classify_error(self, error_type: str, error_message: str) -> ErrorCategory:
        """Classify error into categories."""
        error_text = f"{error_type} {error_message}".lower()
        
        if any(keyword in error_text for keyword in ["connection", "timeout", "network", "socket"]):
            return ErrorCategory.CONNECTION
        elif any(keyword in error_text for keyword in ["401", "403", "unauthorized", "forbidden", "auth"]):
            return ErrorCategory.AUTHENTICATION
        elif any(keyword in error_text for keyword in ["value", "key", "validation", "invalid", "missing"]):
            return ErrorCategory.DATA_VALIDATION
        elif any(keyword in error_text for keyword in ["io", "file", "permission", "disk", "storage"]):
            return ErrorCategory.STORAGE
        elif any(keyword in error_text for keyword in ["config", "setting", "parameter"]):
            return ErrorCategory.CONFIGURATION
        else:
            return ErrorCategory.UNKNOWN
    
    def _attempt_recovery(self, error_info: ErrorInfo) -> Optional[str]:
        """Attempt to recover from an error."""
        category = error_info.category
        
        if category in self.recovery_strategies:
            strategy_info = self.recovery_strategies[category]
            patterns = strategy_info['patterns']
            strategy = strategy_info['strategy']
            
            # Check if error matches any pattern
            error_text = f"{error_info.error_type} {error_info.error_message}".lower()
            if any(pattern.lower() in error_text for pattern in patterns):
                try:
                    return strategy(error_info)
                except Exception as e:
                    self.logger.error(f"Recovery strategy failed: {e}")
        
        return None
    
    def _retry_with_backoff(self, error_info: ErrorInfo) -> str:
        """Retry operation with exponential backoff."""
        if error_info.retry_count < 3:
            error_info.retry_count += 1
            return f"Retry attempt {error_info.retry_count} with exponential backoff"
        return "Max retry attempts reached"
    
    def _handle_auth_error(self, error_info: ErrorInfo) -> str:
        """Handle authentication errors."""
        return "Check API credentials and permissions"
    
    def _handle_validation_error(self, error_info: ErrorInfo) -> str:
        """Handle data validation errors."""
        return "Validate input data and check data format"
    
    def _handle_storage_error(self, error_info: ErrorInfo) -> str:
        """Handle storage errors."""
        return "Check disk space and file permissions"
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours."""
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_errors = [
            error for error in self.error_log
            if datetime.fromisoformat(error['timestamp']) > cutoff_time
        ]
        
        if not recent_errors:
            return {
                "total_errors": 0,
                "by_severity": {},
                "by_category": {},
                "by_component": {},
                "top_errors": []
            }
        
        # Count by severity
        by_severity = {}
        for error in recent_errors:
            severity = error['severity']
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count by category
        by_category = {}
        for error in recent_errors:
            category = error['category']
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by component
        by_component = {}
        for error in recent_errors:
            component = error['component']
            by_component[component] = by_component.get(component, 0) + 1
        
        # Top errors (most frequent)
        error_counts = {}
        for error in recent_errors:
            error_key = f"{error['error_type']}: {error['error_message'][:50]}"
            error_counts[error_key] = error_counts.get(error_key, 0) + 1
        
        top_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_errors": len(recent_errors),
            "by_severity": by_severity,
            "by_category": by_category,
            "by_component": by_component,
            "top_errors": [{"error": error, "count": count} for error, count in top_errors]
        }
    
    def mark_error_resolved(self, error_id: str) -> bool:
        """Mark an error as resolved."""
        for error in self.error_log:
            if error['error_id'] == error_id:
                error['resolved'] = True
                self._save_error_log()
                return True
        return False


# Global error handler instance
error_handler = ErrorHandler()


def handle_errors(
    component: str,
    operation: str,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    context: Optional[Dict[str, Any]] = None
):
    """Decorator for automatic error handling."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_info = error_handler.handle_error(
                    e, component, operation, context, severity
                )
                raise
        return wrapper
    return decorator
