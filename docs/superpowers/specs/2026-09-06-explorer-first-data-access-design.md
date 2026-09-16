# Explorer-first data access — design

**Date:** 2026-09-06
**Status:** Approved (pending spec review)
**Component:** `lineage-mcp` server

## Summary

Add the Lineage block explorer REST API
(`https://explorer.lineage.to/api/v1`, OpenAPI 3.1) as the primary data
source for the MCP server, with the Python SDK used to verify results
against on-chain state.

The guiding pattern: **look up in the explorer first (fast, indexed,
searchable), then verify on-chain via the SDK.** The explorer has
everything indexed and supports capabilities the SDK cannot offer at all
(metadata search, paginated listings, chain status).

## Goals

- Route overlapping point lookups through the explorer, then verify them
  on-chain and report a verification status to the caller.
- Expose the explorer's new capabilities as MCP tools: item metadata
  search, paginated listings of blocks / transactions / address history,
  and chain status.
- Degrade gracefully: never fail a lookup merely because verification
  could not run; surface real explorer/chain disagreements loudly.

## Non-goals

- No write operations (the explorer API is read-only).
- No caching layer (YAGNI for now).
- No change to wallet key tools (`generate-seed-phrase`,
  `generate-keypair`) or `health` / `version`.

## Explorer API surface (reference)

Base path `/api/v1`. All read-only `GET`.

| Endpoint | Purpose |
|---|---|
| `/blocks` (limit, offset, order) | List blocks |
| `/blocks/{id}` | Block by height **or** hash |
| `/blocks/{id}/transactions` | A block's transactions |
| `/transactions` (limit, offset, order) | List transactions (excludes coinbase) |
| `/transactions/{hash}` | Transaction by hash |
| `/addresses/{address}` | Address balance |
| `/addresses/{address}/transactions` (limit, offset) | Address tx history |
| `/items` (q, genesis, limit, offset) | Search minted items by metadata substring / genesis |
| `/supply` | Circulating and total supply |
| `/status` | Chain and indexer status |

Key response schemas: `BlockSummary{num,hash,previousHash,timestamp,version,nbTx}`,
`Transaction{hash,blockHash,version,timestamp,type,inputs,outputs}`,
`Address{address,balance,balanceLngx}`,
`Supply{circulating,circulatingLngx,total,totalLngx,ticker}`,
`Status{network,ticker,height,blocks,transactions}`,
`ItemOutput{genesisHash,metadata,address,amount,amountLngx,spent,txHash,n,blockNum,blockHash,timestamp}`.
List endpoints wrap results as `{data:[...], pagination:{total,limit,offset,hasMore}}`.
Errors use RFC 7807 `Problem{type,title,status,detail,instance}`.

## Architecture

Follows the existing file-per-concern layout. Three new modules plus small
edits to config and server wiring.

```
tool handler (server.py)
   → tools_explorer.<tool>()
       1. ExplorerClient.<endpoint>()          # PRIMARY (fast, indexed)
       2. verify.<kind>(explorer_obj, sdk_fn)  # on-chain re-fetch + compare
   → { ok, source, verified, verification, data }   # overlap tools
   → { ok, source:'explorer', data, pagination }    # explorer-only tools
```

### `explorer.py` — `ExplorerClient`

- Thin, synchronous `httpx` wrapper. One method per endpoint used.
- Base URL and timeout from config (`LINEAGE_EXPLORER_URL`,
  `LINEAGE_EXPLORER_TIMEOUT_S`).
- Each method returns parsed JSON on `2xx`. On non-2xx or transport error
  it raises `ExplorerError(status, message)` (carrying the `Problem`
  detail when present) so callers can distinguish "not found" (404) from
  "unreachable" (timeout/connection).
- No shared global state; instantiated per call from config (matches how
  `create_blockchain_client` is used today).

Methods: `get_block(id)`, `list_blocks(limit, offset, order)`,
`list_block_transactions(id)`, `get_transaction(hash)`,
`list_transactions(limit, offset, order)`, `get_address(address)`,
`list_address_transactions(address, limit, offset)`,
`search_items(q, genesis, limit, offset)`, `get_supply()`, `get_status()`.

### `verify.py` — on-chain verification

Pure functions that take the explorer object and a callable that performs
the SDK lookup, and return a `verification` dict plus a tri-state
`verified`. Verification never raises; a chain error becomes
`'unverified'`.

```python
def verify_against_chain(explorer_obj, sdk_call, compare) -> tuple[verified, verification]
```

- `sdk_call()` returns the SDK `IResult`.
- `compare(explorer_obj, chain_payload) -> (matched: bool, chain_value)`
  is supplied per tool (compares the identity field, see table).
- Result:
  - SDK ok and `matched` → `verified=True`
  - SDK ok and not `matched` → `verified=False`
  - SDK `is_err` / raises → `verified='unverified'` (note carries reason)
- `verification = {method:'sdk', matched, chain_value, note}`.

### `tools_explorer.py` — tools

Composes `ExplorerClient` + SDK (via existing `create_blockchain_client` /
wallet path). Overlap tools implement the resolution flow below; explorer-
only tools just return the explorer payload.

## Behavior — overlap tools

Return shape:

```json
{
  "ok": true,
  "source": "explorer",
  "verified": true,
  "verification": {"method": "sdk", "matched": true, "chain_value": "...", "note": null},
  "data": { "...explorer payload..." }
}
```

Resolution / degradation (per approved design):

```
explorer ok + chain matches    → source:'explorer', verified:true
explorer ok + chain differs     → source:'explorer', verified:false     (mismatch; both values in verification)
explorer ok + chain unreachable → source:'explorer', verified:'unverified'
explorer down + chain ok        → source:'chain',    verified:true       (data from SDK)
both down                        → { ok:false, error }
```

- Per-call `verify` argument (default `true`). When `false`, skip the SDK
  round-trip and return `verified:'skipped'` (no `verification` block).
- On explorer-down fallback, `data` is the SDK payload (pass-through, as in
  the current `tools_blockchain`), and `verified:true` because it *is* the
  chain.

### Overlap tool → verify mapping

| Tool | Args | Explorer call | SDK verify | `matched` compares |
|---|---|---|---|---|
| `get-block` | `id` (height or hash), `verify=true` | `/blocks/{id}` | `get_block_by_num(num)` | block `hash` |
| `get-transaction` | `hash`, `verify=true` | `/transactions/{hash}` | `get_transaction_by_hash(hash)` | tx exists + `hash` |
| `get-address-balance` | `address`, `verify=true` | `/addresses/{address}` | `fetch_balance([address])` | balance amount (timing-tolerant, see below) |
| `get-supply` | `verify=true` | `/supply` | `get_total_supply()` | `total` |
| `get-latest-block` | `verify=true` | `/blocks?order=desc&limit=1` | `get_latest_block()` | height + `hash` |

**Balance verification is timing-sensitive.** A block mined between the
explorer read and the SDK read makes balances legitimately differ. So for
`get-address-balance`, `verified:false` means "amounts differ at query
time (may reflect chain progression, not corruption)"; both amounts are
included in `verification`. It is never a hard failure.

## Behavior — explorer-only tools

No SDK equivalent, so no verification. Return:

```json
{ "ok": true, "source": "explorer", "data": [...], "pagination": {...} }
```

(Single-object endpoints like `get-status` return `data` as an object and
omit `pagination`.)

| Tool | Args | Explorer call |
|---|---|---|
| `list-blocks` | `limit=20, offset=0, order='desc'` | `/blocks` |
| `list-transactions` | `limit=20, offset=0, order='desc'` | `/transactions` |
| `list-block-transactions` | `id` | `/blocks/{id}/transactions` |
| `list-address-transactions` | `address, limit=20, offset=0` | `/addresses/{address}/transactions` |
| `search-items` | `q=None, genesis=None, limit=20, offset=0` | `/items` |
| `get-status` | — | `/status` |

If the explorer is unreachable, explorer-only tools return
`{ok:false, error}` (there is no fallback source).

## Final tool surface

- **SDK-only (unchanged / retained):** `health`, `version`,
  `generate-seed-phrase`, `generate-keypair`, `get-entry-by-hash`,
  `fetch-transactions`.
- **Overlap (explorer-first + verify):** `get-block`, `get-transaction`,
  `get-address-balance`, `get-supply`, `get-latest-block`.
- **Explorer-only:** `list-blocks`, `list-transactions`,
  `list-block-transactions`, `list-address-transactions`, `search-items`,
  `get-status`.

**Removed** (superseded by overlap tools): `get-block-by-number`,
`get-transaction-by-hash`, `get-total-supply`, `get-issued-supply`,
`fetch-balance`.

## Configuration

Added to `AppConfig` (`config.py`) and `.env.example`:

| Env var | Default | Meaning |
|---|---|---|
| `LINEAGE_EXPLORER_URL` | `https://explorer.lineage.to` | Explorer API base |
| `LINEAGE_EXPLORER_TIMEOUT_S` | `10` | Per-request timeout (seconds) |

The explorer API is public and read-only; no auth. Existing SDK env vars
(`LINEAGE_STORAGE_HOST`, `LINEAGE_MEMPOOL_HOST`, `LINEAGE_API_KEY`, …) are
unchanged and still used for the verification / SDK-only path.

## Dependencies

- Add **`httpx`** as an explicit runtime dependency (currently a dev-only
  extra; already vendored for tests). Cleaner than relying on the SDK's
  transitive `requests`.

## Testing

Fully offline unit tests (mirroring the current suite):

- `ExplorerClient`: mocked HTTP (monkeypatch transport / `respx`) — success,
  404 → `ExplorerError(404)`, timeout → `ExplorerError` (unreachable).
- `verify.py`: fake SDK returning ok-match, ok-mismatch, and error/raise →
  asserts `verified` `True` / `False` / `'unverified'`.
- Overlap tools: mocked explorer + fake SDK for each degradation branch,
  including explorer-down fallback and `verify=false` → `'skipped'`.
- Explorer-only tools: mocked explorer, including unreachable → `ok:false`.
- Existing tests remain green.

End-to-end: live server smoke test over Streamable HTTP driving
`get-status`, `search-items`, and one overlap tool. The explorer is
reachable from the dev environment even though a chain node may not be, so
overlap tools are expected to return `verified:'unverified'` there — which
itself validates the degradation path.

## Risks / open questions

- **Explorer vs SDK response shapes differ.** Mitigated: overlap tools
  return the explorer payload as `data`; verification compares only a
  single identity field per tool, not whole objects.
- **Balance/supply timing races.** Handled explicitly (timing-tolerant
  verification, both values surfaced).
- **`get-block` by hash needs the height for SDK verify.** The explorer
  block payload includes `num`; use it to drive `get_block_by_num` for the
  on-chain compare.
```
