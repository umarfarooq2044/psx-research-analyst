import time
import functools
import logging
import sys
from typing import Callable, Type, Tuple, Union

# Configure robust logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("IronClad")

def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: int = 2,
    exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = (Exception,)
):
    """
    Decorator: Institutional-grade exponential backoff retry logic.
    Refuses to crash on transient network errors.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            x = 0
            while True:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    x += 1
                    if x > retries:
                        logger.error(f"❌ CRITICAL FAILURE in {func.__name__} after {retries} attempts. Error: {e}")
                        raise # Give up after max retries
                        
                    sleep_time = backoff_in_seconds * (2 ** (x - 1))
                    logger.warning(f"⚠️ Transient Error in {func.__name__}: {e}. Retrying in {sleep_time}s... ({x}/{retries})")
                    time.sleep(sleep_time)
        return wrapper
    return decorator

def safe_execute(default_return=None):
    """
    Decorator: Never crash. Return specific default value on failure.
    Use for non-critical components (e.g., getting a single news headline).
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"🛡️ IronClad Shield: Caught crash in {func.__name__}. Continuing safely. Error: {e}")
                return default_return
        return wrapper
    return decorator
