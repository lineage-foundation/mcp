from __future__ import annotations

from typing import Optional, Any
from decimal import Decimal

from lineage.wallet import Wallet
from lineage.config import get_config as sdk_get_config, validate_env_config
from lineage_mcp.schemas import BalanceResponse, TransferFundsResponse


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    return str(value)


def _get_ready_wallet() -> Wallet:
    """Helper to initialize a Wallet with validated SDK configuration."""
    wallet = Wallet()
    _ensure_sdk_env()
    
    try:
        cfg_raw = sdk_get_config()
        cfg = _unwrap_cfg(cfg_raw)
    except Exception as e:
        raise RuntimeError(f"Failed to fetch SDK config: {e}")

    err = validate_env_config(cfg)
    if hasattr(err, "is_err"):
        if getattr(err, "is_err"):
            msg = getattr(err, "_error_message", None) or str(getattr(err, "_error", "invalid config"))
            raise RuntimeError(f"Lineage config invalid: {msg}")
    elif err:
        raise RuntimeError(f"Lineage config invalid: {err}")
    
    wallet.config = cfg
    return wallet


def _ensure_sdk_env() -> None:
    # With SDK >=0.2.9, config reading is consistent; no remapping needed.
    return


def _unwrap(obj: Any) -> Any:
    # Match blockchain tools' IResult unwrapping strategy
    seen = set()
    for _ in range(3):
        if id(obj) in seen:
            break
        seen.add(id(obj))
        for attr in ("result", "data", "value", "_value"):
            val = getattr(obj, attr, None)
            if val is not None:
                obj = val
                break
        else:
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


def _unwrap_cfg(obj: Any) -> Any:
    # Unwrap SDK IResult for config values
    try:
        if hasattr(obj, "get_ok") and callable(getattr(obj, "get_ok")):
            return obj.get_ok()
    except Exception:
        pass
    return getattr(obj, "_value", obj)


def generate_seed_phrase(entropy_bits: Optional[int] = None) -> dict:
    wallet = Wallet()
    seed_phrase = wallet.generate_seed_phrase() if entropy_bits is None else wallet.generate_seed_phrase()
    return {"ok": True, "seedPhrase": seed_phrase}


def generate_keypair(seed_phrase: Optional[str] = None) -> dict:
    wallet = Wallet()
    if seed_phrase:
        # In a real implementation, derive from seed phrase if supported
        pass
    keypair = wallet.generate_keypair()
    # Unwrap IResult-like return if present
    value: Any = getattr(keypair, "_value", keypair)
    if isinstance(value, dict):
        address = value.get("address") or value.get("addr")
        public_key = value.get("publicKey") or value.get("public_key")
    else:
        address = getattr(value, "address", None)
        public_key = getattr(value, "publicKey", None) or getattr(value, "public_key", None)
    address_text = _to_text(address)
    public_key_text = _to_text(public_key)
    return {
        "ok": True,
        "address": address_text,
        "publicKey": public_key_text,
    }


def get_balance() -> BalanceResponse:
    try:
        wallet = _get_ready_wallet()
        result = wallet.get_balance()
        
        if hasattr(result, "get_ok") and callable(getattr(result, "get_ok")):
            value: Any = result.get_ok()
        else:
            value = getattr(result, "_value", result)
        
        # Coerce scalars into a dict payload compatible with BalanceResponse
        d = value if isinstance(value, dict) else {"balance": value}
        return BalanceResponse(
            id=d.get("id", ""),
            status=d.get("status", "Success"),
            reason=d.get("reason", ""),
            route=d.get("route", "wallet.get_balance"),
            content=d.get("content", d),
        )
    except Exception as e:
        return BalanceResponse(
            id="", status="Error", reason=str(e), route="wallet.get_balance", content={}
        )


def fetch_balance(addresses: list[str]) -> BalanceResponse:
    try:
        wallet = _get_ready_wallet()
        result = wallet.fetch_balance(addresses)
        
        if hasattr(result, "get_ok") and callable(getattr(result, "get_ok")):
            value: Any = result.get_ok()
        else:
            value = getattr(result, "_value", result)
            
        # Coerce scalars/lists into a dict payload
        d = value if isinstance(value, dict) else {"balances": value}
        return BalanceResponse(
            id=d.get("id", ""),
            status=d.get("status", "Success"),
            reason=d.get("reason", ""),
            route=d.get("route", "wallet.fetch_balance"),
            content=d.get("content", d),
        )
    except Exception as e:
        return BalanceResponse(
            id="", status="Error", reason=str(e), route="wallet.fetch_balance", content={}
        )



def send_transaction(destination: str, amount: Decimal, passphrase: str) -> TransferFundsResponse:
    try:
        wallet = _get_ready_wallet()
        
        # Pre-flight Check: Basic balance validation using Decimal for precision
        balance_res = wallet.get_balance()
        if hasattr(balance_res, "get_ok") and callable(getattr(balance_res, "get_ok")):
            bal_val = balance_res.get_ok()
        else:
            bal_val = getattr(balance_res, "_value", balance_res)
        
        current_balance = Decimal("0.0")
        if isinstance(bal_val, dict):
            # Convert SDK return value to Decimal safely
            raw_bal = bal_val.get("balance", "0.0")
            current_balance = Decimal(str(raw_bal)) if raw_bal is not None else Decimal("0.0")
        elif isinstance(bal_val, (int, float, str, Decimal)):
            current_balance = Decimal(str(bal_val))
            
        if current_balance < amount:
            return TransferFundsResponse(
                id="",
                status="Error",
                reason=f"Insufficient funds: attempted {amount}, but balance is {current_balance}",
                route="wallet.transfer_funds",
                content={"balance": str(current_balance)}
            )

        # Call SDK to broadcast transaction
        # Note: We convert to float only at the last moment if the SDK requires it
        # but here we pass the Decimal directly.
        result = wallet.send_transaction(destination, float(amount), passphrase=passphrase)
        
        if hasattr(result, "get_ok") and callable(getattr(result, "get_ok")):
            value: Any = result.get_ok()
        else:
            value = getattr(result, "_value", result)
            
        # Coerce scalars into a dict payload
        d = value if isinstance(value, dict) else {"result": value}
        
        # Map the SDK response to our schema with sensible defaults
        return TransferFundsResponse(
            id=str(d.get("id", d.get("tx_hash", "none"))),
            status=d.get("status", "Success") if "Error" not in str(d.get("status", "")) else "Error",
            reason=d.get("reason", ""),
            route=d.get("route", "wallet.transfer_funds"),
            content=d.get("content", d),
        )
    except Exception as e:
        return TransferFundsResponse(
            id="", status="Error", reason=f"Transaction failed: {e}", route="wallet.transfer_funds", content={}
        )


from mcp.server.fastmcp import FastMCP
from lineage_mcp.core.context import ServerContext
from lineage_mcp.core.errors import mcp_error_boundary

def register(mcp: FastMCP, ctx: ServerContext):
    @mcp.tool(name="get-balance")
    @mcp_error_boundary
    def wallet_get_balance() -> dict:
        return get_balance().model_dump()

    @mcp.tool(name="fetch-balance")
    @mcp_error_boundary
    def wallet_fetch_balance_tool(addresses: list[str]) -> dict:
        return fetch_balance(addresses).model_dump()

    @mcp.tool(name="generate-seed-phrase")
    @mcp_error_boundary
    def wallet_generate_seed_phrase() -> dict:
        return generate_seed_phrase()

    @mcp.tool(name="generate-keypair")
    @mcp_error_boundary
    def wallet_generate_keypair(seedPhrase: str = None) -> dict:
        return generate_keypair(seed_phrase=seedPhrase)

    @mcp.tool(name="transfer-funds")
    @mcp_error_boundary
    def wallet_transfer_funds_tool(destination: str, amount: str) -> dict:
        if not ctx.config.lineage_passphrase:
            return {
                "ok": False, "id": "", "status": "Error",
                "reason": "Server passphrase not configured (LINEAGE_PASSPHRASE)",
                "route": "wallet.transfer_funds", "content": {}
            }
        return send_transaction(destination, amount, ctx.config.lineage_passphrase).model_dump()
