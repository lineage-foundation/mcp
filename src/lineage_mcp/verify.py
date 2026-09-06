from __future__ import annotations

from typing import Any, Callable


def deep_get(payload: Any, key: str) -> Any:
    """Return the first value for `key` found anywhere in a nested structure."""
    if isinstance(payload, dict):
        if key in payload:
            return payload[key]
        for v in payload.values():
            found = deep_get(v, key)
            if found is not None:
                return found
    elif isinstance(payload, (list, tuple)):
        for item in payload:
            found = deep_get(item, key)
            if found is not None:
                return found
    return None


def verify_against_chain(
    explorer_obj: Any,
    sdk_call: Callable[[], Any],
    compare: Callable[[Any, Any], tuple[bool, Any]],
) -> tuple[bool | str, dict]:
    """Re-fetch on-chain and compare against the explorer object.

    Returns (verified, verification). `verified` is True (matched),
    False (chain returned a different value), or "unverified" (chain
    unreachable / errored).
    """
    try:
        result = sdk_call()
    except Exception as e:  # noqa: BLE001 - any SDK/transport failure is "unverified"
        return "unverified", {"method": "sdk", "matched": None, "chain_value": None,
                              "note": f"chain error: {e}"}

    if not result.is_ok:
        note = result.error_message or str(result.error) or "chain error"
        return "unverified", {"method": "sdk", "matched": None, "chain_value": None, "note": note}

    try:
        matched, chain_value = compare(explorer_obj, result.get_ok())
    except Exception as e:  # noqa: BLE001 - a bad payload/compare must not break the tri-state
        return "unverified", {"method": "sdk", "matched": None, "chain_value": None,
                              "note": f"verification error: {e}"}
    if matched is None:
        return "unverified", {"method": "sdk", "matched": None, "chain_value": chain_value,
                              "note": "chain payload had no comparable field"}
    return matched, {"method": "sdk", "matched": matched, "chain_value": chain_value, "note": None}
