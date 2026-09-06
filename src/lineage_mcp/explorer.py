from __future__ import annotations

from typing import Any, Optional

import httpx

_PREFIX = "/api/v1"


class ExplorerError(Exception):
    """Raised when an explorer request fails.

    status is the HTTP status for a non-2xx response, or None for a
    transport-level error (timeout / connection refused). Callers use this
    to distinguish a definitive 4xx (e.g. not found) from "explorer down".
    """

    def __init__(self, message: str, status: Optional[int] = None) -> None:
        self.status = status
        self.message = message
        super().__init__(f"{status} {message}" if status is not None else message)


class ExplorerClient:
    def __init__(
        self,
        base_url: str = "https://explorer.lineage.to",
        timeout: float = 10.0,
        *,
        client: Optional[httpx.Client] = None,
    ) -> None:
        self._client = client or httpx.Client(base_url=base_url, timeout=timeout)

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        # Drop None-valued params so they are not serialized.
        clean = {k: v for k, v in (params or {}).items() if v is not None}
        try:
            resp = self._client.get(f"{_PREFIX}{path}", params=clean)
        except httpx.HTTPError as e:
            raise ExplorerError(str(e) or e.__class__.__name__, status=None) from e
        if resp.status_code >= 400:
            title = ""
            try:
                body = resp.json()
                title = body.get("title") or body.get("detail") or ""
            except Exception:
                title = resp.text[:200]
            raise ExplorerError(title or "request failed", status=resp.status_code)
        return resp.json()

    def get_block(self, id: str | int) -> dict:  # noqa: A002
        return self._get(f"/blocks/{id}")

    def list_blocks(self, limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
        return self._get("/blocks", {"limit": limit, "offset": offset, "order": order})

    def list_block_transactions(self, id: str | int) -> dict:  # noqa: A002
        return self._get(f"/blocks/{id}/transactions")

    def get_transaction(self, tx_hash: str) -> dict:
        return self._get(f"/transactions/{tx_hash}")

    def list_transactions(self, limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
        return self._get("/transactions", {"limit": limit, "offset": offset, "order": order})

    def get_address(self, address: str) -> dict:
        return self._get(f"/addresses/{address}")

    def list_address_transactions(self, address: str, limit: int = 20, offset: int = 0) -> dict:
        return self._get(f"/addresses/{address}/transactions", {"limit": limit, "offset": offset})

    def search_items(self, q: Optional[str] = None, genesis: Optional[str] = None,
                     limit: int = 20, offset: int = 0) -> dict:
        return self._get("/items", {"q": q, "genesis": genesis, "limit": limit, "offset": offset})

    def get_supply(self) -> dict:
        return self._get("/supply")

    def get_status(self) -> dict:
        return self._get("/status")
