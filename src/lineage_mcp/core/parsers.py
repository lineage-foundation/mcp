from typing import Any

def unwrap_sdk_result(result: Any) -> Any:
    """Deterministically extracts the value from an SDK IResult."""
    try:
        if hasattr(result, "get_ok") and callable(getattr(result, "get_ok")):
            return result.get_ok()
    except Exception:
        pass
    return getattr(result, "_value", result)
