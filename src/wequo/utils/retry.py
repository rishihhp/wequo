"""
Robust retry logic with exponential backoff and circuit breaker patterns.
"""

import time
import logging
import random
from functools import wraps
from typing import Callable, Any, Optional, List, Type
from dataclasses import dataclass
from enum import Enum


class RetryStrategy(Enum):
    """Retry strategies."""
    FIXED = "fixed"
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    RANDOM = "random"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL
    backoff_multiplier: float = 2.0
    jitter: bool = True
    retryable_exceptions: List[Type[Exception]] = None
    
    def __post_init__(self):
        if self.retryable_exceptions is None:
            self.retryable_exceptions = [
                ConnectionError,
                TimeoutError,
                OSError,
                Exception  # Generic fallback
            ]


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: float = 60.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        self.logger = logging.getLogger(__name__)
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                self.logger.info("Circuit breaker transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == "HALF_OPEN":
            return True
        return False
    
    def record_success(self):
        """Record a successful execution."""
        self.failure_count = 0
        if self.state == "HALF_OPEN":
            self.state = "CLOSED"
            self.logger.info("Circuit breaker transitioning to CLOSED")
    
    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    circuit_breaker: Optional[CircuitBreaker] = None,
    logger: Optional[logging.Logger] = None
):
    """
    Decorator for retry logic with exponential backoff and circuit breaker.
    
    Args:
        config: Retry configuration
        circuit_breaker: Circuit breaker instance
        logger: Logger instance
    """
    if config is None:
        config = RetryConfig()
    if logger is None:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                # Check circuit breaker
                if circuit_breaker and not circuit_breaker.can_execute():
                    raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record success in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_success()
                    
                    if attempt > 0:
                        logger.info(f"{func.__name__} succeeded on attempt {attempt + 1}")
                    
                    return result
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.error(f"{func.__name__} failed with non-retryable exception: {e}")
                        raise e
                    
                    # Record failure in circuit breaker
                    if circuit_breaker:
                        circuit_breaker.record_failure()
                    
                    if attempt == config.max_attempts - 1:
                        logger.error(f"{func.__name__} failed after {config.max_attempts} attempts: {e}")
                        raise e
                    
                    # Calculate delay
                    delay = _calculate_delay(attempt, config)
                    
                    logger.warning(f"{func.__name__} failed on attempt {attempt + 1}: {e}. Retrying in {delay:.2f}s")
                    time.sleep(delay)
            
            # This should never be reached, but just in case
            raise last_exception
        
        return wrapper
    return decorator


def _calculate_delay(attempt: int, config: RetryConfig) -> float:
    """Calculate delay based on retry strategy."""
    if config.strategy == RetryStrategy.FIXED:
        delay = config.base_delay
    elif config.strategy == RetryStrategy.EXPONENTIAL:
        delay = config.base_delay * (config.backoff_multiplier ** attempt)
    elif config.strategy == RetryStrategy.LINEAR:
        delay = config.base_delay * (attempt + 1)
    elif config.strategy == RetryStrategy.RANDOM:
        delay = random.uniform(config.base_delay, config.base_delay * 2)
    else:
        delay = config.base_delay
    
    # Apply jitter
    if config.jitter:
        jitter_range = delay * 0.1  # 10% jitter
        delay += random.uniform(-jitter_range, jitter_range)
    
    # Cap at max delay
    delay = min(delay, config.max_delay)
    
    return max(0, delay)


class RetryManager:
    """Centralized retry management for the WeQuo system."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.circuit_breakers = {}
        
        # Default configurations for different operations
        self.configs = {
            "api_call": RetryConfig(
                max_attempts=3,
                base_delay=1.0,
                max_delay=30.0,
                strategy=RetryStrategy.EXPONENTIAL,
                retryable_exceptions=[ConnectionError, TimeoutError, OSError]
            ),
            "data_processing": RetryConfig(
                max_attempts=2,
                base_delay=0.5,
                max_delay=10.0,
                strategy=RetryStrategy.FIXED,
                retryable_exceptions=[Exception]
            ),
            "file_operation": RetryConfig(
                max_attempts=3,
                base_delay=0.5,
                max_delay=15.0,
                strategy=RetryStrategy.EXPONENTIAL,
                retryable_exceptions=[OSError, IOError]
            )
        }
    
    def get_circuit_breaker(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 60.0) -> CircuitBreaker:
        """Get or create a circuit breaker for a specific operation."""
        if name not in self.circuit_breakers:
            self.circuit_breakers[name] = CircuitBreaker(failure_threshold, recovery_timeout)
        return self.circuit_breakers[name]
    
    def retry_api_call(self, func: Callable) -> Callable:
        """Decorator for API calls with retry logic."""
        circuit_breaker = self.get_circuit_breaker("api_calls", failure_threshold=3, recovery_timeout=300.0)
        return retry_with_backoff(
            config=self.configs["api_call"],
            circuit_breaker=circuit_breaker,
            logger=self.logger
        )(func)
    
    def retry_data_processing(self, func: Callable) -> Callable:
        """Decorator for data processing operations with retry logic."""
        return retry_with_backoff(
            config=self.configs["data_processing"],
            logger=self.logger
        )(func)
    
    def retry_file_operation(self, func: Callable) -> Callable:
        """Decorator for file operations with retry logic."""
        circuit_breaker = self.get_circuit_breaker("file_operations", failure_threshold=5, recovery_timeout=120.0)
        return retry_with_backoff(
            config=self.configs["file_operation"],
            circuit_breaker=circuit_breaker,
            logger=self.logger
        )(func)
    
    def get_circuit_breaker_status(self) -> dict:
        """Get status of all circuit breakers."""
        status = {}
        for name, cb in self.circuit_breakers.items():
            status[name] = {
                "state": cb.state,
                "failure_count": cb.failure_count,
                "last_failure_time": cb.last_failure_time
            }
        return status


# Global retry manager instance
retry_manager = RetryManager()
