from __future__ import annotations

import os
from typing import Any, Optional

import lineage
from lineage.wallet import Wallet


def _to_hex(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        return value.hex()
    return str(value)


def _keypair_dict(keypair: Any) -> dict:
    return {
        "ok": True,
        "address": _to_hex(getattr(keypair, "address", None)),
        "publicKey": _to_hex(getattr(keypair, "public_key", None)),
    }


def generate_seed_phrase() -> dict:
    return {"ok": True, "seedPhrase": lineage.generate_seed_phrase()}


def generate_keypair(seed_phrase: Optional[str] = None) -> dict:
    if seed_phrase:
        # Deterministically derive the keypair from the seed phrase, offline.
        wallet = Wallet()
        config = {"passphrase": os.environ.get("LINEAGE_PASSPHRASE", "")}
        result = wallet.from_seed(seed_phrase, config, init_offline=True)
        if not result.is_ok:
            return {"ok": False, "error": result.error_message or str(result.error)}
        return _keypair_dict(wallet.current_keypair)

    result = lineage.generate_keypair()
    if not result.is_ok:
        return {"ok": False, "error": result.error_message or str(result.error)}
    return _keypair_dict(result.get_ok())


def fetch_balance(addresses: list[str]) -> dict:
    # fetch_balance needs network routes (mempool/storage host) but no wallet
    # seed, so we configure the network from environment and query directly.
    cfg_result = lineage.get_config()
    if not cfg_result.is_ok:
        return {"ok": False, "error": cfg_result.error_message or str(cfg_result.error)}

    wallet = Wallet()
    init = wallet.init_network(cfg_result.get_ok())
    if not init.is_ok:
        return {"ok": False, "error": init.error_message or str(init.error)}

    result = wallet.fetch_balance(addresses)
    if not result.is_ok:
        return {"ok": False, "error": result.error_message or str(result.error)}

    payload = result.get_ok()
    return payload if isinstance(payload, dict) else {"ok": True, "balances": payload}


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


def send_transaction(destination: str, amount: int, seed_phrase: str) -> dict:
    """Broadcast a payment of `amount` (base units) to `destination`.

    Requires a seed phrase to derive a spendable wallet (the reworked SDK signs
    from keypairs, not a passphrase alone). The network config — including the
    passphrase — comes from the environment via lineage.get_config().
    create_transactions enforces sufficient funds on-chain and returns an error
    result if the balance is too low.
    """
    if not seed_phrase:
        return {"ok": False, "error": "Server seed phrase not configured (LINEAGE_SEED_PHRASE)"}

    cfg_result = lineage.get_config()
    if not cfg_result.is_ok:
        return {"ok": False, "error": cfg_result.error_message or str(cfg_result.error)}

    wallet = Wallet()
    seeded = wallet.from_seed(seed_phrase, cfg_result.get_ok())
    if not seeded.is_ok:
        return {"ok": False, "error": seeded.error_message or str(seeded.error)}

    result = wallet.create_transactions(destination_address=destination, amount=amount)
    if not result.is_ok:
        return {"ok": False, "error": result.error_message or str(result.error)}

    payload = result.get_ok()
    return payload if isinstance(payload, dict) else {"ok": True, "result": payload}
