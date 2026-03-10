from __future__ import annotations

from typing import Optional

from lineage.wallet import Wallet
from lineage.config import get_config as sdk_get_config, validate_env_config
from typing import Any
from .schemas import BalanceResponse


def _to_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    return str(value)


def _as_dict(obj: object) -> dict:  # unused; retained only if needed later
    if isinstance(obj, dict):
        return obj
    return {"value": repr(obj)}



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
    wallet = Wallet()
    # Ensure network config is present for internal init_network path
    _ensure_sdk_env()
    cfg_raw = sdk_get_config()
    cfg = _unwrap_cfg(cfg_raw)
    err = validate_env_config(cfg)
    # Treat only error IResult as failure; ignore ok IResult objects
    if hasattr(err, "is_err"):
        if getattr(err, "is_err"):
            msg = getattr(err, "_error_message", None) or str(getattr(err, "_error", "invalid config"))
            raise RuntimeError(f"Lineage config invalid: {msg}")
    elif err:
        raise RuntimeError(f"Lineage config invalid: {err}")
    wallet.config = cfg
    # SDK get_balance returns balance for the current wallet address
    result = wallet.get_balance()
    if hasattr(result, "get_ok") and callable(getattr(result, "get_ok")):
        value: Any = result.get_ok()
    else:
        value = getattr(result, "_value", result)
    # Coerce scalars into a dict payload compatible with BalanceResponse
    d = value if isinstance(value, dict) else {"balance": value}
    return BalanceResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


def fetch_balance(addresses: list[str]) -> BalanceResponse:
    wallet = Wallet()
    # Ensure SDK config is set before network operations
    _ensure_sdk_env()
    try:
        cfg_raw = sdk_get_config()
        cfg = _unwrap_cfg(cfg_raw)
    except Exception as e:
        return BalanceResponse(id="", status="Error", reason=f"get_config failed: {e}", route="wallet.fetch_balance", content={})
    try:
        err = validate_env_config(cfg)
        if hasattr(err, "is_err"):
            if getattr(err, "is_err"):
                msg = getattr(err, "_error_message", None) or str(getattr(err, "_error", "invalid config"))
                return BalanceResponse(id="", status="Error", reason=msg, route="wallet.fetch_balance", content={})
        elif err:
            return BalanceResponse(id="", status="Error", reason=str(err), route="wallet.fetch_balance", content={})
    except Exception as e:
        return BalanceResponse(id="", status="Error", reason=f"validate_env_config failed: {e}", route="wallet.fetch_balance", content={})
    wallet.config = cfg
    # Initialize routes explicitly to avoid None internal config usage
    # SDK >=0.2.9: no explicit init_network required
    # Call SDK
    result = wallet.fetch_balance(addresses)
    if hasattr(result, "get_ok") and callable(getattr(result, "get_ok")):
        value: Any = result.get_ok()
    else:
        value = getattr(result, "_value", result)
    # Coerce scalars/lists into a dict payload
    d = value if isinstance(value, dict) else {"balances": value}
    return BalanceResponse(
        id=d.get("id", ""),
        status=d.get("status", ""),
        reason=d.get("reason", ""),
        route=d.get("route", ""),
        content=d.get("content", d),
    )


