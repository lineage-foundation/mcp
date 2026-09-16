from __future__ import annotations

from typing import Any, Callable, Optional

from .explorer import ExplorerError
from .verify import deep_get, verify_against_chain


def _explorer_only(fetch: Callable[[], Any], *, paginated: bool = True) -> dict:
    try:
        payload = fetch()
    except ExplorerError as e:
        return {"ok": False, "error": str(e), "status": e.status}
    if paginated:
        return {
            "ok": True,
            "source": "explorer",
            "data": payload.get("data"),
            "pagination": payload.get("pagination"),
        }
    return {"ok": True, "source": "explorer", "data": payload}


def list_blocks(explorer, limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
    return _explorer_only(lambda: explorer.list_blocks(limit=limit, offset=offset, order=order))


def list_transactions(explorer, limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
    return _explorer_only(lambda: explorer.list_transactions(limit=limit, offset=offset, order=order))


def list_block_transactions(explorer, id: str) -> dict:  # noqa: A002
    return _explorer_only(lambda: explorer.list_block_transactions(id))


def list_address_transactions(explorer, address: str, limit: int = 20, offset: int = 0) -> dict:
    return _explorer_only(lambda: explorer.list_address_transactions(address, limit=limit, offset=offset))


def search_items(explorer, q: Optional[str] = None, genesis: Optional[str] = None,
                 limit: int = 20, offset: int = 0) -> dict:
    if not q and not genesis:
        return {"ok": False, "error": "Provide at least one of 'q' or 'genesis'."}
    return _explorer_only(
        lambda: explorer.search_items(q=q, genesis=genesis, limit=limit, offset=offset)
    )


def get_status(explorer) -> dict:
    return _explorer_only(explorer.get_status, paginated=False)


def _chain_fallback(sdk_call: Callable[[], Any], explorer_error: ExplorerError) -> dict:
    try:
        result = sdk_call()
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": f"explorer unavailable ({explorer_error}); chain error: {e}"}
    if not result.is_ok:
        note = result.error_message or str(result.error) or "chain error"
        return {"ok": False, "error": f"explorer unavailable ({explorer_error}); chain error: {note}"}
    payload = result.get_ok()
    data = payload if isinstance(payload, dict) else {"value": payload}
    return {"ok": True, "source": "chain", "verified": True, "data": data}


def _resolve_overlap(explorer_fetch, sdk_call, compare, verify: bool) -> dict:
    try:
        obj = explorer_fetch()
    except ExplorerError as e:
        # 4xx is a definitive client error (e.g. not found) -> no fallback.
        if e.status is not None and 400 <= e.status < 500:
            return {"ok": False, "error": str(e), "status": e.status}
        # transport error / 5xx -> explorer is "down" -> verify against chain directly.
        return _chain_fallback(sdk_call, e)

    if not verify:
        return {"ok": True, "source": "explorer", "verified": "skipped", "data": obj}

    verified, verification = verify_against_chain(obj, sdk_call, compare)
    return {"ok": True, "source": "explorer", "verified": verified,
            "verification": verification, "data": obj}


def _compare_key(key: str):
    def cmp(explorer_obj, chain_payload):
        chain_value = deep_get(chain_payload, key)
        if chain_value is None:
            return None, None  # field not locatable on-chain -> "unverified", not a mismatch
        return chain_value == explorer_obj.get(key), chain_value
    return cmp


def get_block(explorer, sdk_call, id, verify: bool = True) -> dict:  # noqa: A002
    return _resolve_overlap(lambda: explorer.get_block(id), sdk_call, _compare_key("hash"), verify)


def get_transaction(explorer, sdk_call, tx_hash: str, verify: bool = True) -> dict:
    return _resolve_overlap(lambda: explorer.get_transaction(tx_hash), sdk_call, _compare_key("hash"), verify)


def get_address_balance(explorer, sdk_call, address: str, verify: bool = True) -> dict:
    # Balance verification is timing-sensitive; a mismatch may reflect chain
    # progression rather than corruption. We still report it, never hard-fail.
    return _resolve_overlap(lambda: explorer.get_address(address), sdk_call, _compare_key("balance"), verify)


def get_supply(explorer, sdk_call, verify: bool = True) -> dict:
    return _resolve_overlap(explorer.get_supply, sdk_call, _compare_key("total"), verify)


def get_latest_block(explorer, sdk_call, verify: bool = True) -> dict:
    def fetch():
        payload = explorer.list_blocks(limit=1, offset=0, order="desc")
        data = payload.get("data") or []
        if not data:
            raise ExplorerError("no blocks", status=404)
        return data[0]
    return _resolve_overlap(fetch, sdk_call, _compare_key("hash"), verify)
