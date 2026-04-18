from __future__ import annotations

from lineage.blockchain import BlockchainClient
from typing import Any

from lineage_mcp.schemas import (
    BalanceRequest,
    BalanceResponse,
    LatestBlockResponse,
    LatestBlockContent,
    Block,
    BlockHeader,
    SupplyResponse,
    EntryResponse,
    TransactionResponse,
    TransactionsResponse,
)


def _as_dict(obj: object) -> dict:
    # Try common ways to convert SDK objects to plain dicts
    if isinstance(obj, dict):
        return obj
    for attr in ("to_dict", "model_dump"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    # Fallback to attribute extraction for known fields
    keys = ("height", "hash", "timestamp")
    data = {k: getattr(obj, k, None) for k in keys}
    # If nothing useful, return repr
    if not any(v is not None for v in data.values()):
        return {"value": repr(obj)}
    return data


def _unwrap(obj: Any) -> Any:
    # Iteratively unwrap common result wrappers (e.g., IResult-like: result/data)
    seen = set()
    for _ in range(3):
        if id(obj) in seen:
            break
        seen.add(id(obj))
        # attr-based unwrap
        for attr in ("result", "data", "value", "_value"):
            val = getattr(obj, attr, None)
            if val is not None:
                obj = val
                break
        else:
            # dict-based unwrap
            if isinstance(obj, dict):
                for key in ("result", "data", "value"):
                    if key in obj:
                        obj = obj[key]
                        break
                else:
                    break
            else:
                break
    return obj


def _find_value(obj: Any, keys: list[str]) -> Any:
    # Recursively search dicts/lists/objects for the first matching key
    if isinstance(obj, dict):
        for k in keys:
            if k in obj:
                return obj[k]
        for v in obj.values():
            found = _find_value(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_value(item, keys)
            if found is not None:
                return found
    else:
        for k in keys:
            val = getattr(obj, k, None)
            if val is not None:
                return val
    return None


def get_latest_block(client: BlockchainClient) -> LatestBlockResponse:
    v = _unwrap(client.get_latest_block())
    d = v if isinstance(v, dict) else _as_dict(v)

    # Map fields exactly as provided by the SDK result
    header = d["content"]["block"]["header"]
    header_model = BlockHeader(
        version=header["version"],
        bits=header["bits"],
        nonce_and_mining_tx_hash=header["nonce_and_mining_tx_hash"],
        b_num=header["b_num"],
        timestamp=header["timestamp"],
        difficulty=header["difficulty"],
        seed_value=header["seed_value"],
        previous_hash=header["previous_hash"],
        txs_merkle_root_and_hash=header["txs_merkle_root_and_hash"],
    )
    block_model = Block(header=header_model, transactions=d["content"]["block"].get("transactions", []))
    content_model = LatestBlockContent(block=block_model)

    return LatestBlockResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=content_model,
    )


def get_balance(client: BlockchainClient, req: BalanceRequest) -> BalanceResponse:
    # Use the SDK's balance-by-address method on the Blockchain client
    v = _unwrap(client.get_balance_for_address(req.address))
    d = v if isinstance(v, dict) else _as_dict(v)
    return BalanceResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def get_total_supply(client: BlockchainClient) -> SupplyResponse:
    v = _unwrap(client.get_total_supply())
    if isinstance(v, dict):
        return SupplyResponse(
            id=v.get("id", ""),
            status=v.get("status", ""),
            reason=v.get("reason", ""),
            route=v.get("route", ""),
            content=v.get("content", v),
        )
    # SDK may return a plain number
    return SupplyResponse(id="", status="", reason="", route="", content=v)


def get_issued_supply(client: BlockchainClient) -> SupplyResponse:
    v = _unwrap(client.get_issued_supply())
    if isinstance(v, dict):
        return SupplyResponse(
            id=v.get("id", ""),
            status=v.get("status", ""),
            reason=v.get("reason", ""),
            route=v.get("route", ""),
            content=v.get("content", v),
        )
    return SupplyResponse(id="", status="", reason="", route="", content=v)



def get_block_by_number(client: BlockchainClient, block_num: int) -> LatestBlockResponse:
    v = _unwrap(client.get_block_by_num(block_num))
    d = v if isinstance(v, dict) else _as_dict(v)
    header = _find_value(d, ["header"]) or {}
    header_model = BlockHeader(
        version=header["version"],
        bits=header["bits"],
        nonce_and_mining_tx_hash=header["nonce_and_mining_tx_hash"],
        b_num=header["b_num"],
        timestamp=header["timestamp"],
        difficulty=header["difficulty"],
        seed_value=header["seed_value"],
        previous_hash=header["previous_hash"],
        txs_merkle_root_and_hash=header["txs_merkle_root_and_hash"],
    )
    block_node = _find_value(d, ["block"]) or {}
    transactions = block_node.get("transactions", []) if isinstance(block_node, dict) else []
    block_model = Block(header=header_model, transactions=transactions)
    content_model = LatestBlockContent(block=block_model)
    return LatestBlockResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=content_model,
    )


def get_entry_by_hash(client: BlockchainClient, hash: str) -> EntryResponse:  # noqa: A002 (shadow builtins)
    v = _unwrap(client.get_blockchain_entry(hash))
    d = v if isinstance(v, dict) else _as_dict(v)
    return EntryResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def get_transaction_by_hash(client: BlockchainClient, tx_hash: str) -> TransactionResponse:
    v = _unwrap(client.get_transaction_by_hash(tx_hash))
    d = v if isinstance(v, dict) else _as_dict(v)
    return TransactionResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def fetch_transactions(client: BlockchainClient, tx_hashes: list[str]) -> TransactionsResponse:
    v = _unwrap(client.fetch_transactions(tx_hashes))
    d = v if isinstance(v, dict) else _as_dict(v)
    return TransactionsResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )

