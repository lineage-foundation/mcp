from functools import wraps
import logging
from typing import Callable

logger = logging.getLogger(__name__)

def mcp_error_boundary(func: Callable) -> Callable:
    """
    Catches exceptions and wraps them in a structured LLM-friendly JSON response.
    This prevents the LLM from receiving raw stack traces that break execution loops.
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> dict:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}", exc_info=True)
            return {
                "ok": False,
                "status": "error",
                "reason": str(e),
                "recoverable": False,
                "route": func.__name__,
                "content": {}
            }
    return wrapper
