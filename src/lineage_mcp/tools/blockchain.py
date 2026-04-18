from __future__ import annotations

from mcp.server.fastmcp import FastMCP
from lineage_mcp.core.context import ServerContext
from lineage_mcp.core.errors import mcp_error_boundary

from lineage.blockchain import BlockchainClient
from typing import Any
from lineage_mcp.utils import unwrap_sdk_result

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
    v = unwrap_sdk_result(client.get_latest_block())
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
    v = unwrap_sdk_result(client.get_balance_for_address(req.address))
    d = v if isinstance(v, dict) else _as_dict(v)
    return BalanceResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def get_total_supply(client: BlockchainClient) -> SupplyResponse:
    v = unwrap_sdk_result(client.get_total_supply())
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
    v = unwrap_sdk_result(client.get_issued_supply())
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
    v = unwrap_sdk_result(client.get_block_by_num(block_num))
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
    v = unwrap_sdk_result(client.get_blockchain_entry(hash))
    d = v if isinstance(v, dict) else _as_dict(v)
    return EntryResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def get_transaction_by_hash(client: BlockchainClient, tx_hash: str) -> TransactionResponse:
    v = unwrap_sdk_result(client.get_transaction_by_hash(tx_hash))
    d = v if isinstance(v, dict) else _as_dict(v)
    return TransactionResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def fetch_transactions(client: BlockchainClient, tx_hashes: list[str]) -> TransactionsResponse:
    v = unwrap_sdk_result(client.fetch_transactions(tx_hashes))
    d = v if isinstance(v, dict) else _as_dict(v)
    return TransactionsResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )



def register(mcp: FastMCP, ctx: ServerContext):
    @mcp.tool(name="get-latest-block")
    @mcp_error_boundary
    def blockchain_get_latest_block() -> dict:
        return get_latest_block(ctx.blockchain_client).model_dump()

    @mcp.tool(name="get-total-supply")
    @mcp_error_boundary
    def blockchain_get_total_supply() -> dict:
        return get_total_supply(ctx.blockchain_client).model_dump()

    @mcp.tool(name="get-issued-supply")
    @mcp_error_boundary
    def blockchain_get_issued_supply() -> dict:
        return get_issued_supply(ctx.blockchain_client).model_dump()

    @mcp.tool(name="get-block-by-number")
    @mcp_error_boundary
    def blockchain_get_block_by_number(height: int) -> dict:
        return get_block_by_number(ctx.blockchain_client, height).model_dump()

    @mcp.tool(name="get-entry-by-hash")
    @mcp_error_boundary
    def blockchain_get_entry_by_hash(hash: str) -> dict:
        return get_entry_by_hash(ctx.blockchain_client, hash).model_dump()

    @mcp.tool(name="get-transaction-by-hash")
    @mcp_error_boundary
    def blockchain_get_transaction_by_hash(tx_hash: str) -> dict:
        return get_transaction_by_hash(ctx.blockchain_client, tx_hash).model_dump()

    @mcp.tool(name="fetch-transactions")
    @mcp_error_boundary
    def blockchain_fetch_transactions(tx_hashes: list[str]) -> dict:
        return fetch_transactions(ctx.blockchain_client, tx_hashes).model_dump()
