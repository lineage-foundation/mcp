from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from typing import Any, List


class BalanceRequest(BaseModel):
    address: str = Field(..., description="Hex-encoded address")

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str) -> str:
        if not isinstance(v, str) or not v:
            raise ValueError("address must be a non-empty string")
        return v


class BalanceResponse(BaseModel):
    ok: bool = True
    id: str
    status: str
    reason: str
    route: str
    content: Any


class BlockHeader(BaseModel):
    version: int
    bits: Any
    nonce_and_mining_tx_hash: Any
    b_num: int
    timestamp: int
    difficulty: Any
    seed_value: Any
    previous_hash: str
    txs_merkle_root_and_hash: Any


class Block(BaseModel):
    header: BlockHeader
    transactions: Any


class LatestBlockContent(BaseModel):
    block: Block


class LatestBlockResponse(BaseModel):
    ok: bool = True
    id: str
    status: str
    reason: str
    route: str
    content: LatestBlockContent


class SupplyResponse(BaseModel):
    ok: bool = True
    id: str
    status: str
    reason: str
    route: str
    content: Any

 
class EntryResponse(BaseModel):
    ok: bool = True
    id: str
    status: str
    reason: str
    route: str
    content: Any


class TransactionResponse(BaseModel):
    ok: bool = True
    id: str
    status: str
    reason: str
    route: str
    content: Any


class TransactionsResponse(BaseModel):
    ok: bool = True
    id: str
    status: str
    reason: str
    route: str
    content: Any


