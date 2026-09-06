from lineage.interfaces import IResult

from lineage_mcp import tools_wallet
from lineage_mcp.tools_wallet import generate_seed_phrase, generate_keypair, send_transaction


def test_generate_seed_phrase():
    resp = generate_seed_phrase()
    assert resp["ok"] is True
    assert len(resp["seedPhrase"].split()) >= 12


def test_generate_keypair_random():
    resp = generate_keypair()
    assert resp["ok"] is True
    # address is a hex string, publicKey is hex-encoded from bytes
    assert isinstance(resp["address"], str) and resp["address"]
    assert isinstance(resp["publicKey"], str) and resp["publicKey"]


def test_generate_keypair_from_seed_is_deterministic():
    resp = generate_seed_phrase()
    seed = resp["seedPhrase"]
    a = generate_keypair(seed_phrase=seed)
    b = generate_keypair(seed_phrase=seed)
    assert a["address"] == b["address"]


class _FakeWallet:
    """Records the last create_transactions call; no network."""

    last = None

    def from_seed(self, seed, config, init_offline=False):
        return IResult.ok(True)

    def create_transactions(self, destination_address, amount):
        _FakeWallet.last = (destination_address, amount)
        return IResult.ok({"transaction_hash": "tx1", "to": destination_address, "amount": amount})


def test_send_transaction_requires_seed():
    resp = send_transaction("dest", 100, "")
    assert resp["ok"] is False
    assert "seed" in resp["error"].lower()


def test_send_transaction_success_passes_int_amount(monkeypatch):
    import lineage
    monkeypatch.setattr(
        lineage, "get_config",
        lambda: IResult.ok({"mempoolHost": "m", "storageHost": "s", "passphrase": "p"}),
    )
    monkeypatch.setattr(tools_wallet, "Wallet", _FakeWallet)
    resp = send_transaction("addrX", 500, "twelve word seed phrase here ...")
    assert resp["transaction_hash"] == "tx1"
    # amount forwarded verbatim as an int in base units
    assert _FakeWallet.last == ("addrX", 500)


def test_send_transaction_surfaces_sdk_error(monkeypatch):
    import lineage
    monkeypatch.setattr(
        lineage, "get_config",
        lambda: IResult.ok({"mempoolHost": "m", "storageHost": "s", "passphrase": "p"}),
    )

    class _BrokeWallet(_FakeWallet):
        def create_transactions(self, destination_address, amount):
            return IResult.err("insufficient funds")

    monkeypatch.setattr(tools_wallet, "Wallet", _BrokeWallet)
    resp = send_transaction("addrX", 999, "seed")
    assert resp["ok"] is False
    assert "insufficient funds" in resp["error"]
