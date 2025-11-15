"""
Error handling and connection recovery utilities
"""

import asyncio
import logging
from typing import Callable, Any, Optional, TypeVar, Coroutine
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ConnectionError(Exception):
    """Raised when connection fails"""
    pass


class TranscriptionError(Exception):
    """Raised when transcription fails"""
    pass


class AudioStreamError(Exception):
    """Raised when audio streaming fails"""
    pass


async def retry_async(
    func: Callable[..., Coroutine[Any, Any, T]],
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
) -> T:
    """
    Retry an async function with exponential backoff

    Args:
        func: Async function to retry
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay after each retry
        exceptions: Tuple of exceptions to catch and retry
        on_retry: Optional callback called on each retry with (exception, attempt_number)

    Returns:
        Result of the function call

    Raises:
        Last exception if all retries fail
    """
    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e

            if attempt == max_retries:
                logger.error(
                    f"Failed after {max_retries} retries: {e}"
                )
                raise

            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} failed: {e}. "
                f"Retrying in {delay:.1f}s..."
            )

            if on_retry:
                on_retry(e, attempt + 1)

            await asyncio.sleep(delay)
            delay *= backoff_factor

    # Should never reach here, but just in case
    raise last_exception or Exception("Retry failed")


def async_retry(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff

    Usage:
        @async_retry(max_retries=3, initial_delay=1.0)
        async def my_function():
            # Function that might fail
            pass
    """
    def decorator(func: Callable[..., Coroutine[Any, Any, T]]):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async def call():
                return await func(*args, **kwargs)

            return await retry_async(
                call,
                max_retries=max_retries,
                initial_delay=initial_delay,
                backoff_factor=backoff_factor,
                exceptions=exceptions
            )

        return wrapper
    return decorator


class ConnectionHealthMonitor:
    """
    Monitors connection health and triggers reconnection if needed
    """

    def __init__(
        self,
        check_interval: float = 5.0,
        timeout_threshold: float = 30.0
    ):
        """
        Initialize health monitor

        Args:
            check_interval: Interval between health checks in seconds
            timeout_threshold: Time without activity before considering connection dead
        """
        self.check_interval = check_interval
        self.timeout_threshold = timeout_threshold
        self._last_activity = asyncio.get_event_loop().time()
        self._monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._on_connection_lost: Optional[Callable[[], Coroutine]] = None

    def record_activity(self) -> None:
        """Record connection activity"""
        self._last_activity = asyncio.get_event_loop().time()

    def start_monitoring(
        self,
        on_connection_lost: Callable[[], Coroutine]
    ) -> None:
        """
        Start monitoring connection health

        Args:
            on_connection_lost: Async callback to call when connection is lost
        """
        if self._monitoring:
            logger.warning("Health monitor already running")
            return

        self._on_connection_lost = on_connection_lost
        self._monitoring = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Connection health monitoring started")

    async def stop_monitoring(self) -> None:
        """Stop monitoring"""
        self._monitoring = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Connection health monitoring stopped")

    async def _monitor_loop(self) -> None:
        """Monitor loop that checks connection health"""
        try:
            while self._monitoring:
                await asyncio.sleep(self.check_interval)

                time_since_activity = (
                    asyncio.get_event_loop().time() - self._last_activity
                )

                if time_since_activity > self.timeout_threshold:
                    logger.warning(
                        f"No activity for {time_since_activity:.1f}s, "
                        "connection may be lost"
                    )

                    if self._on_connection_lost:
                        try:
                            await self._on_connection_lost()
                        except Exception as e:
                            logger.error(f"Error in connection lost handler: {e}")

                    # Reset timer after calling handler
                    self.record_activity()

        except asyncio.CancelledError:
            logger.info("Health monitor cancelled")
        except Exception as e:
            logger.error(f"Error in health monitor: {e}")


class CircuitBreaker:
    """
    Circuit breaker pattern for preventing repeated failed calls
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_attempts: int = 1
    ):
        """
        Initialize circuit breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time to wait before trying again (seconds)
            half_open_attempts: Number of successful calls needed to close circuit
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_attempts = half_open_attempts

        self._failure_count = 0
        self._success_count = 0
        self._state = "closed"  # closed, open, half_open
        self._opened_at: Optional[float] = None

    async def call(
        self,
        func: Callable[..., Coroutine[Any, Any, T]],
        *args,
        **kwargs
    ) -> T:
        """
        Call a function through the circuit breaker

        Args:
            func: Async function to call
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Result of the function call

        Raises:
            Exception if circuit is open
        """
        if self._state == "open":
            # Check if recovery timeout has passed
            if (
                self._opened_at and
                asyncio.get_event_loop().time() - self._opened_at >= self.recovery_timeout
            ):
                logger.info("Circuit breaker entering half-open state")
                self._state = "half_open"
                self._success_count = 0
            else:
                raise ConnectionError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)

            # Success
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call"""
        if self._state == "half_open":
            self._success_count += 1
            if self._success_count >= self.half_open_attempts:
                logger.info("Circuit breaker closed after successful recovery")
                self._state = "closed"
                self._failure_count = 0
        elif self._state == "closed":
            self._failure_count = 0

    def _on_failure(self) -> None:
        """Handle failed call"""
        self._failure_count += 1

        if self._failure_count >= self.failure_threshold:
            logger.warning(
                f"Circuit breaker opened after {self._failure_count} failures"
            )
            self._state = "open"
            self._opened_at = asyncio.get_event_loop().time()

    def reset(self) -> None:
        """Manually reset circuit breaker"""
        self._state = "closed"
        self._failure_count = 0
        self._success_count = 0
        self._opened_at = None
        logger.info("Circuit breaker manually reset")

    @property
    def state(self) -> str:
        """Get current circuit breaker state"""
        return self._state
