# Explorer-first data access Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Lineage block explorer REST API as the primary data source for the MCP server, verifying overlapping lookups on-chain via the Python SDK.

**Architecture:** A thin `httpx` explorer client (`explorer.py`) and a verification helper (`verify.py`) are composed by tool functions in `tools_explorer.py`. Overlap tools return `{ok, source, verified, verification, data}`; explorer-only tools return `{ok, source:'explorer', data, pagination?}`. `server.py` wires the tools and builds clients from config.

**Tech Stack:** Python 3.14, `httpx` (new runtime dep), `lineage-sdk` 1.0.1, `mcp` 2.x (MCPServer), pytest, ruff.

## Global Constraints

- Python `>=3.11`; dev/CI on 3.14.7. Run tests with `.venv/bin/python -m pytest -q`.
- Deps: `mcp>=2.1,<3`, `pydantic>=2.12`, `lineage-sdk>=1.0.1`. New: `httpx>=0.28`.
- Explorer base default: `https://explorer.lineage.to`; API prefix `/api/v1`. Read-only, no auth.
- All tools return plain `dict`; failures are returned as `{"ok": false, "error": ...}` data, never raised (matches existing tools).
- Tool names are kebab-case. Prompt/other existing tools unchanged.
- Commit after each task. End commit messages with the repo's required trailers (see existing commits).
- ruff must pass: `.venv/bin/ruff check src/ tests/`.

---

## File structure

- Create `src/lineage_mcp/explorer.py` — `ExplorerClient`, `ExplorerError`.
- Create `src/lineage_mcp/verify.py` — `verify_against_chain`.
- Create `src/lineage_mcp/tools_explorer.py` — overlap + explorer-only tool functions.
- Modify `src/lineage_mcp/config.py` — add `explorer_url`, `explorer_timeout_s`.
- Modify `src/lineage_mcp/tools_wallet.py` — add `sdk_fetch_balance_result` (raw IResult for balance verify).
- Modify `src/lineage_mcp/server.py` — register new tools; remove 5 superseded tools.
- Modify `pyproject.toml`, `.env.example`, `README.md`.
- Tests: `tests/test_explorer.py`, `tests/test_verify.py`, `tests/test_tools_explorer.py`.

---

## Task 1: Config, dependency, and env

**Files:**
- Modify: `pyproject.toml` (dependencies)
- Modify: `src/lineage_mcp/config.py`
- Modify: `.env.example`
- Test: `tests/test_config.py` (create)

**Interfaces:**
- Produces: `AppConfig.explorer_url: str`, `AppConfig.explorer_timeout_s: float`; `get_config()` reads `LINEAGE_EXPLORER_URL` (default `https://explorer.lineage.to`) and `LINEAGE_EXPLORER_TIMEOUT_S` (default `10`).

- [ ] **Step 1: Add httpx as a runtime dependency**

In `pyproject.toml`, under `[project].dependencies`, add `httpx` (it is currently only in the `dev` extra):

```toml
dependencies = [
  "lineage-sdk>=1.0.1",
  "python-dotenv>=1.0.1",
  "uvicorn>=0.30.0",
  "mcp>=2.1,<3",
  # >=2.12 ensures pydantic-core has prebuilt cp314 wheels (2.11 pins core 2.33, which
  # has no Python 3.14 wheel and fails to compile). Keeps fresh installs working on latest Python.
  "pydantic>=2.12",
  "httpx>=0.28",
]
```

- [ ] **Step 2: Sync the environment**

Run: `UV_PROJECT_ENVIRONMENT=.venv uv lock && UV_PROJECT_ENVIRONMENT=.venv uv sync --extra dev -p .venv/bin/python`
Expected: resolves; `httpx` present in `.venv`.

- [ ] **Step 3: Write the failing config test**

Create `tests/test_config.py`:

```python
import importlib


def _fresh_config(monkeypatch, **env):
    for k in ("LINEAGE_EXPLORER_URL", "LINEAGE_EXPLORER_TIMEOUT_S"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import lineage_mcp.config as config
    importlib.reload(config)
    return config.get_config()


def test_explorer_defaults(monkeypatch):
    cfg = _fresh_config(monkeypatch)
    assert cfg.explorer_url == "https://explorer.lineage.to"
    assert cfg.explorer_timeout_s == 10.0


def test_explorer_env_override(monkeypatch):
    cfg = _fresh_config(monkeypatch, LINEAGE_EXPLORER_URL="http://x:9/", LINEAGE_EXPLORER_TIMEOUT_S="3.5")
    assert cfg.explorer_url == "http://x:9/"
    assert cfg.explorer_timeout_s == 3.5
```

- [ ] **Step 4: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_config.py -q`
Expected: FAIL (`AppConfig` has no `explorer_url`).

- [ ] **Step 5: Add the config fields**

In `src/lineage_mcp/config.py`, add fields to `AppConfig` and populate them in `get_config()`:

```python
@dataclass(frozen=True)
class AppConfig:
    lineage_passphrase: str
    storage_host: Optional[str]
    mempool_host: Optional[str]
    valence_host: Optional[str]
    api_key: Optional[str]
    explorer_url: str
    explorer_timeout_s: float
    log_level: str


def get_config() -> AppConfig:
    return AppConfig(
        lineage_passphrase=os.environ.get("LINEAGE_PASSPHRASE", ""),
        storage_host=os.environ.get("LINEAGE_STORAGE_HOST"),
        mempool_host=os.environ.get("LINEAGE_MEMPOOL_HOST"),
        valence_host=os.environ.get("LINEAGE_VALENCE_HOST"),
        api_key=os.environ.get("LINEAGE_API_KEY"),
        explorer_url=os.environ.get("LINEAGE_EXPLORER_URL", "https://explorer.lineage.to"),
        explorer_timeout_s=float(os.environ.get("LINEAGE_EXPLORER_TIMEOUT_S", "10")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
```

- [ ] **Step 6: Update `.env.example`**

Add under the Lineage SDK block:

```
# Block explorer (read-only REST API)
LINEAGE_EXPLORER_URL="https://explorer.lineage.to"
LINEAGE_EXPLORER_TIMEOUT_S="10"
```

- [ ] **Step 7: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_config.py -q`
Expected: PASS (2 passed).

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock src/lineage_mcp/config.py .env.example tests/test_config.py
git commit -m "feat: add explorer config (url/timeout) and httpx dependency"
```

---

## Task 2: ExplorerClient + ExplorerError

**Files:**
- Create: `src/lineage_mcp/explorer.py`
- Test: `tests/test_explorer.py`

**Interfaces:**
- Produces:
  - `class ExplorerError(Exception)` with attrs `status: int | None`, `message: str`; `str()` renders `"<status> <message>"` or just message when status is None.
  - `class ExplorerClient`:
    - `__init__(self, base_url="https://explorer.lineage.to", timeout=10.0, *, client: httpx.Client | None = None)`
    - Methods returning parsed JSON (dict), raising `ExplorerError` on non-2xx (status set) or transport error (status None):
      `get_block(id)`, `list_blocks(limit=20, offset=0, order="desc")`,
      `list_block_transactions(id)`, `get_transaction(tx_hash)`,
      `list_transactions(limit=20, offset=0, order="desc")`, `get_address(address)`,
      `list_address_transactions(address, limit=20, offset=0)`,
      `search_items(q=None, genesis=None, limit=20, offset=0)`, `get_supply()`, `get_status()`.

- [ ] **Step 1: Write failing tests**

Create `tests/test_explorer.py`:

```python
import httpx
import pytest

from lineage_mcp.explorer import ExplorerClient, ExplorerError


def _client(handler):
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://explorer.test", transport=transport)
    return ExplorerClient(client=http)


def test_get_status_ok():
    def handler(request):
        assert request.url.path == "/api/v1/status"
        return httpx.Response(200, json={"network": "Lineage", "height": 7017})
    ex = _client(handler)
    assert ex.get_status()["height"] == 7017


def test_list_blocks_builds_query():
    seen = {}
    def handler(request):
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": [], "pagination": {}})
    ex = _client(handler)
    ex.list_blocks(limit=5, offset=10, order="asc")
    assert seen["path"] == "/api/v1/blocks"
    assert seen["params"] == {"limit": "5", "offset": "10", "order": "asc"}


def test_get_transaction_path_encoded():
    def handler(request):
        assert request.url.path == "/api/v1/transactions/abc%20def"
        return httpx.Response(200, json={"hash": "abc def"})
    ex = _client(handler)
    assert ex.get_transaction("abc def")["hash"] == "abc def"


def test_not_found_raises_with_status():
    def handler(request):
        return httpx.Response(404, json={"title": "Transaction not found", "detail": "no"})
    ex = _client(handler)
    with pytest.raises(ExplorerError) as e:
        ex.get_transaction("deadbeef")
    assert e.value.status == 404


def test_transport_error_raises_status_none():
    def handler(request):
        raise httpx.ConnectError("boom")
    ex = _client(handler)
    with pytest.raises(ExplorerError) as e:
        ex.get_status()
    assert e.value.status is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_explorer.py -q`
Expected: FAIL (module `lineage_mcp.explorer` not found).

- [ ] **Step 3: Implement `explorer.py`**

Create `src/lineage_mcp/explorer.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_explorer.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/lineage_mcp/explorer.py tests/test_explorer.py
git commit -m "feat: add ExplorerClient httpx wrapper for the block explorer API"
```

---

## Task 3: On-chain verification helper

**Files:**
- Create: `src/lineage_mcp/verify.py`
- Test: `tests/test_verify.py`

**Interfaces:**
- Produces: `verify_against_chain(explorer_obj, sdk_call, compare) -> tuple[bool | str, dict]`
  - `sdk_call: Callable[[], IResult]` — performs the on-chain lookup.
  - `compare: Callable[[explorer_obj, chain_payload], tuple[bool, Any]]` — returns `(matched, chain_value)`.
  - Returns `(verified, verification)` where `verified` is `True`, `False`, or `"unverified"`, and `verification = {"method": "sdk", "matched": bool | None, "chain_value": Any, "note": str | None}`.
- Also produces helper `deep_get(payload, key) -> Any` (first match of `key` in nested dict/list, else None) used by compare functions in Task 5.

- [ ] **Step 1: Write failing tests**

Create `tests/test_verify.py`:

```python
from lineage.interfaces import IResult

from lineage_mcp.verify import verify_against_chain, deep_get


def _cmp_hash(explorer_obj, chain_payload):
    cv = deep_get(chain_payload, "hash")
    return cv == explorer_obj.get("hash"), cv


def test_match():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.ok({"hash": "h1"}), _cmp_hash)
    assert verified is True
    assert v == {"method": "sdk", "matched": True, "chain_value": "h1", "note": None}


def test_mismatch():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.ok({"hash": "OTHER"}), _cmp_hash)
    assert verified is False
    assert v["matched"] is False and v["chain_value"] == "OTHER"


def test_chain_error_is_unverified():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.err("node down"), _cmp_hash)
    assert verified == "unverified"
    assert v["matched"] is None and "node down" in v["note"]


def test_chain_raises_is_unverified():
    obj = {"hash": "h1"}
    def boom():
        raise RuntimeError("kaboom")
    verified, v = verify_against_chain(obj, boom, _cmp_hash)
    assert verified == "unverified"
    assert "kaboom" in v["note"]


def test_deep_get_nested():
    assert deep_get({"a": {"b": {"hash": "x"}}}, "hash") == "x"
    assert deep_get({"data": [{"num": 5}]}, "num") == 5
    assert deep_get({"a": 1}, "missing") is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_verify.py -q`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement `verify.py`**

Create `src/lineage_mcp/verify.py`:

```python
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

    matched, chain_value = compare(explorer_obj, result.get_ok())
    return matched, {"method": "sdk", "matched": matched, "chain_value": chain_value, "note": None}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_verify.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/lineage_mcp/verify.py tests/test_verify.py
git commit -m "feat: add on-chain verification helper with tri-state result"
```

---

## Task 4: Explorer-only tools

**Files:**
- Create: `src/lineage_mcp/tools_explorer.py`
- Test: `tests/test_tools_explorer.py`

**Interfaces:**
- Produces (all take an `ExplorerClient`-like object as first arg, return `dict`):
  - `list_blocks(explorer, limit=20, offset=0, order="desc")`
  - `list_transactions(explorer, limit=20, offset=0, order="desc")`
  - `list_block_transactions(explorer, id)`
  - `list_address_transactions(explorer, address, limit=20, offset=0)`
  - `search_items(explorer, q=None, genesis=None, limit=20, offset=0)`
  - `get_status(explorer)`
  - Success (list): `{"ok": True, "source": "explorer", "data": [...], "pagination": {...}}`
  - Success (single, e.g. status): `{"ok": True, "source": "explorer", "data": {...}}`
  - Explorer error: `{"ok": False, "error": str, "status": int | None}`
  - `search_items` with neither `q` nor `genesis`: `{"ok": False, "error": "Provide at least one of 'q' or 'genesis'."}`

- [ ] **Step 1: Write failing tests**

Create `tests/test_tools_explorer.py`:

```python
from lineage_mcp import tools_explorer as te
from lineage_mcp.explorer import ExplorerError


class FakeExplorer:
    """Records the last call and returns canned payloads or raises."""

    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error
        self.calls = []

    def _ret(self, name, **kw):
        self.calls.append((name, kw))
        if self._error is not None:
            raise self._error
        return self._payload

    def list_blocks(self, **kw): return self._ret("list_blocks", **kw)
    def list_transactions(self, **kw): return self._ret("list_transactions", **kw)
    def list_block_transactions(self, id): return self._ret("list_block_transactions", id=id)
    def list_address_transactions(self, address, **kw): return self._ret("list_address_transactions", address=address, **kw)
    def search_items(self, **kw): return self._ret("search_items", **kw)
    def get_status(self): return self._ret("get_status")


def test_list_blocks_ok():
    ex = FakeExplorer(payload={"data": [{"num": 1}], "pagination": {"total": 1}})
    resp = te.list_blocks(ex, limit=5)
    assert resp == {"ok": True, "source": "explorer", "data": [{"num": 1}], "pagination": {"total": 1}}
    assert ex.calls[0] == ("list_blocks", {"limit": 5, "offset": 0, "order": "desc"})


def test_get_status_ok_single_object():
    ex = FakeExplorer(payload={"network": "Lineage", "height": 7})
    resp = te.get_status(ex)
    assert resp == {"ok": True, "source": "explorer", "data": {"network": "Lineage", "height": 7}}


def test_search_items_requires_q_or_genesis():
    ex = FakeExplorer(payload={"data": []})
    resp = te.search_items(ex)
    assert resp["ok"] is False and "q" in resp["error"]
    assert ex.calls == []  # never hit the API


def test_search_items_with_q():
    ex = FakeExplorer(payload={"data": [{"genesisHash": "g"}], "pagination": {}})
    resp = te.search_items(ex, q="foo")
    assert resp["ok"] is True and resp["data"] == [{"genesisHash": "g"}]


def test_explorer_error_surfaces_status():
    ex = FakeExplorer(error=ExplorerError("not found", status=404))
    resp = te.list_transactions(ex)
    assert resp == {"ok": False, "error": "404 not found", "status": 404}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_tools_explorer.py -q`
Expected: FAIL (module not found).

- [ ] **Step 3: Implement the explorer-only part of `tools_explorer.py`**

Create `src/lineage_mcp/tools_explorer.py`:

```python
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_tools_explorer.py -q`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add src/lineage_mcp/tools_explorer.py tests/test_tools_explorer.py
git commit -m "feat: add explorer-only tools (listings, item search, status)"
```

---

## Task 5: Overlap tools (explorer-first + verify)

**Files:**
- Modify: `src/lineage_mcp/tools_explorer.py`
- Modify: `src/lineage_mcp/tools_wallet.py` (add `sdk_fetch_balance_result`)
- Test: `tests/test_tools_explorer.py` (append)

**Interfaces:**
- Consumes: `verify_against_chain`, `deep_get` (Task 3); `ExplorerError` (Task 2).
- Produces (in `tools_explorer.py`):
  - `get_block(explorer, sdk_call, id, verify=True)`
  - `get_transaction(explorer, sdk_call, tx_hash, verify=True)`
  - `get_address_balance(explorer, sdk_call, address, verify=True)`
  - `get_supply(explorer, sdk_call, verify=True)`
  - `get_latest_block(explorer, sdk_call, verify=True)`
  - where `sdk_call: Callable[[], IResult]` performs the on-chain lookup.
  - Success: `{"ok": True, "source": "explorer", "verified": True|False|"unverified"|"skipped", "verification": {...} (omitted when skipped), "data": {...}}`
  - Explorer 4xx: `{"ok": False, "error": str, "status": int}` (no fallback).
  - Explorer down (status None or 5xx): fall back to chain → `{"ok": True, "source": "chain", "verified": True, "data": {...}}`; if chain also fails → `{"ok": False, "error": str}`.
- Produces (in `tools_wallet.py`): `sdk_fetch_balance_result(addresses: list[str]) -> IResult` — configures the network and returns the raw SDK `IResult` (used as the balance `sdk_call`).

- [ ] **Step 1: Write failing tests (append to `tests/test_tools_explorer.py`)**

```python
from lineage.interfaces import IResult


def _ok(payload):
    return lambda: IResult.ok(payload)


def _err(msg):
    return lambda: IResult.err(msg)


def test_get_transaction_verified_true():
    ex = FakeExplorer(payload={"hash": "h1", "blockHash": "b1"})
    resp = te.get_transaction(ex, _ok({"hash": "h1"}), "h1")
    assert resp["ok"] is True
    assert resp["source"] == "explorer"
    assert resp["verified"] is True
    assert resp["data"] == {"hash": "h1", "blockHash": "b1"}


def test_get_transaction_mismatch_false():
    ex = FakeExplorer(payload={"hash": "h1"})
    resp = te.get_transaction(ex, _ok({"hash": "DIFFERENT"}), "h1")
    assert resp["verified"] is False
    assert resp["verification"]["chain_value"] == "DIFFERENT"


def test_get_transaction_chain_down_unverified():
    ex = FakeExplorer(payload={"hash": "h1"})
    resp = te.get_transaction(ex, _err("node down"), "h1")
    assert resp["verified"] == "unverified"
    assert resp["source"] == "explorer"
    assert resp["data"] == {"hash": "h1"}


def test_verify_false_skips_chain():
    ex = FakeExplorer(payload={"hash": "h1"})
    called = {"n": 0}
    def sdk():
        called["n"] += 1
        return IResult.ok({"hash": "h1"})
    resp = te.get_transaction(ex, sdk, "h1", verify=False)
    assert resp["verified"] == "skipped"
    assert "verification" not in resp
    assert called["n"] == 0


def test_explorer_down_falls_back_to_chain():
    ex = FakeExplorer(error=ExplorerError("timeout", status=None))
    resp = te.get_transaction(ex, _ok({"hash": "h1", "onchain": True}), "h1")
    assert resp["ok"] is True
    assert resp["source"] == "chain"
    assert resp["verified"] is True
    assert resp["data"] == {"hash": "h1", "onchain": True}


def test_explorer_404_does_not_fall_back():
    ex = FakeExplorer(error=ExplorerError("not found", status=404))
    resp = te.get_transaction(ex, _ok({"hash": "h1"}), "h1")
    assert resp["ok"] is False
    assert resp["status"] == 404


def test_both_down_returns_error():
    ex = FakeExplorer(error=ExplorerError("timeout", status=None))
    resp = te.get_transaction(ex, _err("node down"), "h1")
    assert resp["ok"] is False
    assert "node down" in resp["error"]


def test_get_supply_verified_on_total():
    ex = FakeExplorer(payload={"total": "360360000000000000", "circulating": "9"})
    resp = te.get_supply(ex, _ok({"total": "360360000000000000"}))
    assert resp["verified"] is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv/bin/python -m pytest tests/test_tools_explorer.py -q`
Expected: FAIL (`get_transaction` / `get_supply` not defined).

- [ ] **Step 3: Add the overlap resolver + tools to `tools_explorer.py`**

Add imports at the top of `src/lineage_mcp/tools_explorer.py`:

```python
from .verify import deep_get, verify_against_chain
```

Append:

```python
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
        return (chain_value is not None and chain_value == explorer_obj.get(key)), chain_value
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
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv/bin/python -m pytest tests/test_tools_explorer.py -q`
Expected: PASS (all).

- [ ] **Step 5: Add `sdk_fetch_balance_result` to `tools_wallet.py`**

Append to `src/lineage_mcp/tools_wallet.py`:

```python
def sdk_fetch_balance_result(addresses: list[str]):
    """Return the raw SDK IResult for a balance lookup (for on-chain verify).

    Unlike fetch_balance (which returns a friendly dict), this preserves the
    IResult so callers can distinguish ok/err for verification.
    """
    cfg_result = lineage.get_config()
    if not cfg_result.is_ok:
        return cfg_result
    wallet = Wallet()
    init = wallet.init_network(cfg_result.get_ok())
    if not init.is_ok:
        return init
    return wallet.fetch_balance(addresses)
```

- [ ] **Step 6: Verify existing wallet tests still pass**

Run: `.venv/bin/python -m pytest tests/test_tools_wallet.py -q`
Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add src/lineage_mcp/tools_explorer.py src/lineage_mcp/tools_wallet.py tests/test_tools_explorer.py
git commit -m "feat: add explorer-first overlap tools with on-chain verification"
```

---

## Task 6: Wire tools into the server; remove superseded tools

**Files:**
- Modify: `src/lineage_mcp/server.py`
- Modify: `README.md`
- Test: `tests/test_server_import.py` (append a registration assertion)

**Interfaces:**
- Consumes: everything from Tasks 2–5, plus existing `create_blockchain_client`, `get_config`.
- Final tool set (see spec). Removed: `get-block-by-number`, `get-transaction-by-hash`, `get-total-supply`, `get-issued-supply`, `fetch-balance`.

- [ ] **Step 1: Write a failing registration test**

Append to `tests/test_server_import.py`:

```python
import anyio


def test_expected_tool_names():
    from lineage_mcp.server import mcp
    names = {t.name for t in anyio.run(mcp.list_tools)}
    expected = {
        "health", "version", "generate-seed-phrase", "generate-keypair",
        "get-entry-by-hash", "fetch-transactions",
        "get-block", "get-transaction", "get-address-balance", "get-supply", "get-latest-block",
        "list-blocks", "list-transactions", "list-block-transactions",
        "list-address-transactions", "search-items", "get-status",
    }
    assert names == expected
    removed = {"get-block-by-number", "get-transaction-by-hash", "get-total-supply",
               "get-issued-supply", "fetch-balance"}
    assert names.isdisjoint(removed)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_server_import.py::test_expected_tool_names -q`
Expected: FAIL (new tools absent, old tools present).

- [ ] **Step 3: Update imports in `server.py`**

Replace the tools imports block. Keep only the SDK-only blockchain tools still in use (`get_entry_by_hash`, `fetch_transactions`); add explorer wiring:

```python
from .clients import create_blockchain_client
from .config import get_config
from .explorer import ExplorerClient
from .tools_blockchain import (
    get_entry_by_hash,
    get_transaction_by_hash,
    fetch_transactions,
)
from .tools_wallet import fetch_balance as wallet_fetch_balance  # noqa: F401  (kept? see step 4)
from .tools_wallet import sdk_fetch_balance_result
from .tools_health import health as health_impl, version as version_impl
from .tools_wallet import generate_seed_phrase as gen_seed_impl, generate_keypair as gen_keypair_impl
from . import prompts as prompt_catalog
from . import tools_explorer as te
```

Note: `get_transaction_by_hash` from `tools_blockchain` is used as the `sdk_call` for the `get-transaction` overlap tool. `wallet_fetch_balance` is no longer used once `fetch-balance` is removed — delete that import line to keep ruff clean.

- [ ] **Step 4: Replace the blockchain/balance tool handlers**

Remove these handlers entirely: `blockchain_get_latest_block` (old), `wallet_fetch_balance_tool` (fetch-balance), `blockchain_get_total_supply`, `blockchain_get_issued_supply`, `blockchain_get_block_by_number`, `blockchain_get_transaction_by_hash`.

Keep `blockchain_get_entry_by_hash` and `blockchain_fetch_transactions` as-is.

Add a helper and the new handlers (place after the `version` tool):

```python
def _explorer() -> ExplorerClient:
    cfg = get_config()
    return ExplorerClient(cfg.explorer_url, cfg.explorer_timeout_s)


# --- Overlap tools (explorer-first + on-chain verify) ---

@mcp.tool(name="get-latest-block")
def get_latest_block(verify: bool = True) -> dict:
    cfg = get_config()
    sdk = create_blockchain_client(cfg)
    return te.get_latest_block(_explorer(), lambda: sdk.get_latest_block(), verify=verify)


@mcp.tool(name="get-block")
def get_block(id: str, verify: bool = True) -> dict:  # noqa: A002
    cfg = get_config()
    sdk = create_blockchain_client(cfg)
    # Verify the on-chain block by its height; the explorer accepts height or hash.
    return te.get_block(_explorer(), lambda: sdk.get_block_by_num(int(id)) if str(id).isdigit()
                        else sdk.get_blockchain_entry(id), id, verify=verify)


@mcp.tool(name="get-transaction")
def get_transaction(hash: str, verify: bool = True) -> dict:  # noqa: A002
    cfg = get_config()
    sdk = create_blockchain_client(cfg)
    return te.get_transaction(_explorer(), lambda: sdk.get_transaction_by_hash(hash), hash, verify=verify)


@mcp.tool(name="get-address-balance")
def get_address_balance(address: str, verify: bool = True) -> dict:
    return te.get_address_balance(_explorer(), lambda: sdk_fetch_balance_result([address]), address, verify=verify)


@mcp.tool(name="get-supply")
def get_supply(verify: bool = True) -> dict:
    cfg = get_config()
    sdk = create_blockchain_client(cfg)
    return te.get_supply(_explorer(), lambda: sdk.get_total_supply(), verify=verify)


# --- Explorer-only tools ---

@mcp.tool(name="list-blocks")
def list_blocks(limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
    return te.list_blocks(_explorer(), limit=limit, offset=offset, order=order)


@mcp.tool(name="list-transactions")
def list_transactions(limit: int = 20, offset: int = 0, order: str = "desc") -> dict:
    return te.list_transactions(_explorer(), limit=limit, offset=offset, order=order)


@mcp.tool(name="list-block-transactions")
def list_block_transactions(id: str) -> dict:  # noqa: A002
    return te.list_block_transactions(_explorer(), id)


@mcp.tool(name="list-address-transactions")
def list_address_transactions(address: str, limit: int = 20, offset: int = 0) -> dict:
    return te.list_address_transactions(_explorer(), address, limit=limit, offset=offset)


@mcp.tool(name="search-items")
def search_items(q: Optional[str] = None, genesis: Optional[str] = None,
                 limit: int = 20, offset: int = 0) -> dict:
    return te.search_items(_explorer(), q=q, genesis=genesis, limit=limit, offset=offset)


@mcp.tool(name="get-status")
def get_status() -> dict:
    return te.get_status(_explorer())
```

Ensure `from .tools_blockchain import ... get_transaction_by_hash ...` is only imported if used; here the handlers call `sdk.get_transaction_by_hash` directly on the client, so remove `get_transaction_by_hash` from the `tools_blockchain` import (it is a client method, not a `tools_blockchain` function). Final `tools_blockchain` import should be exactly:

```python
from .tools_blockchain import get_entry_by_hash, fetch_transactions
```

- [ ] **Step 5: Run the registration test + full suite + ruff**

Run: `.venv/bin/python -m pytest -q && .venv/bin/ruff check src/ tests/`
Expected: PASS; ruff clean. Fix any unused imports (e.g. remove the `wallet_fetch_balance` import).

- [ ] **Step 6: Update README tool list**

In `README.md`, replace the "Try tools" line with:

```
  - Try tools: `get-status`, `search-items`, `list-blocks`, `get-block`, `get-transaction`, `get-address-balance`, `get-supply`, `generate-seed-phrase`, `health`, `version`.
```

- [ ] **Step 7: End-to-end smoke test**

Start the server (loopback) and drive a few tools:

Run:
```bash
LINEAGE_PASSPHRASE=test .venv/bin/uvicorn lineage_mcp.server:app --host 127.0.0.1 --port 8145 --log-level warning &
sleep 2
call() { curl -s -X POST http://127.0.0.1:8145/mcp -H 'Content-Type: application/json' -H 'Accept: application/json, text/event-stream' -d "$1" | sed -n 's/^data: //p'; }
call '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | .venv/bin/python -c "import sys,json;print(len(json.load(sys.stdin)['result']['tools']),'tools')"
call '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"get-status","arguments":{}}}' | .venv/bin/python -c "import sys,json;print(json.loads(json.load(sys.stdin)['result']['content'][0]['text']))"
call '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"get-latest-block","arguments":{}}}' | .venv/bin/python -c "import sys,json;d=json.loads(json.load(sys.stdin)['result']['content'][0]['text']);print('source',d.get('source'),'verified',d.get('verified'))"
kill %1
```
Expected: `17 tools`; `get-status` returns the live chain status dict; `get-latest-block` returns `source explorer` with `verified unverified` (chain node not reachable from this env) — proving explorer-first works and the verify path degrades correctly.

- [ ] **Step 8: Commit**

```bash
git add src/lineage_mcp/server.py README.md tests/test_server_import.py
git commit -m "feat: wire explorer-first tools into server; remove superseded SDK tools"
```

---

## Self-Review

**Spec coverage:**
- Explorer client (all endpoints) → Task 2. ✓
- Tri-state verification + degradation → Task 3 (helper) + Task 5 (resolver/fallback). ✓
- Overlap tools + verify mapping table → Task 5. ✓
- Explorer-only tools → Task 4. ✓
- Removed/kept tool surface → Task 6. ✓
- Config (`LINEAGE_EXPLORER_URL`, `LINEAGE_EXPLORER_TIMEOUT_S`) → Task 1. ✓
- `httpx` runtime dep → Task 1. ✓
- Testing strategy (mocked HTTP, fake SDK, e2e smoke) → Tasks 2–6. ✓
- `verify` per-call arg default true → Task 5 + Task 6 handlers. ✓
- Balance timing tolerance → Task 5 (`get_address_balance` comment; never hard-fails since `verified:false` is still `ok:true`). ✓

**Placeholder scan:** none — every step has concrete code/commands.

**Type consistency:** `sdk_call` is `Callable[[], IResult]` across Tasks 3, 5, 6. `ExplorerError(message, status)` consistent (Task 2 constructor, Tasks 4/5 usage). Overlap return keys (`ok/source/verified/verification/data`) consistent across Task 5 impl and tests and Task 6 smoke. `deep_get`/`verify_against_chain` names consistent Task 3 ↔ Task 5.

**Note on verification field extraction:** `_compare_key` uses `deep_get` against the SDK payload, whose exact on-chain shape is unverified (no node access in dev). The verification *framework* is correct and unit-tested with controlled fakes; the specific compared field paths (`hash`, `total`, `balance`) may need tuning against a live node — call this out during execution when a node is available.
