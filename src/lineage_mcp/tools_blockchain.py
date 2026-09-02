from __future__ import annotations

from typing import Any

from lineage.blockchain import BlockchainClient
from lineage.interfaces import IResult


def _payload(result: IResult) -> dict:
    """Return the SDK result's payload verbatim, or a structured error.

    The lineage SDK returns an ``IResult``. On success we surface ``get_ok()``
    unchanged (the tool exposes exactly what the SDK reports); a non-dict
    payload (e.g. a bare supply figure) is wrapped so the tool keeps a dict
    return type. On failure we surface the SDK's own error message as data
    so the caller sees why, rather than an opaque tool-execution error.
    """
    if not result.is_ok:
        return {"ok": False, "error": result.error_message or str(result.error) or "Lineage SDK error"}
    value: Any = result.get_ok()
    return value if isinstance(value, dict) else {"value": value}


def get_latest_block(client: BlockchainClient) -> dict:
    return _payload(client.get_latest_block())


def get_total_supply(client: BlockchainClient) -> dict:
    return _payload(client.get_total_supply())


def get_issued_supply(client: BlockchainClient) -> dict:
    return _payload(client.get_issued_supply())


def get_block_by_number(client: BlockchainClient, block_num: int) -> dict:
    return _payload(client.get_block_by_num(block_num))


def get_entry_by_hash(client: BlockchainClient, block_hash: str) -> dict:
    return _payload(client.get_blockchain_entry(block_hash))


def get_transaction_by_hash(client: BlockchainClient, tx_hash: str) -> dict:
    return _payload(client.get_transaction_by_hash(tx_hash))


def fetch_transactions(client: BlockchainClient, tx_hashes: list[str]) -> dict:
    return _payload(client.fetch_transactions(tx_hashes))
