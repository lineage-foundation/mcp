from __future__ import annotations

from typing import Any, Callable, Optional

from .explorer import ExplorerError


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
