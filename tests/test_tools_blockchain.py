from types import SimpleNamespace

from lineage_mcp.schemas import BalanceRequest
from lineage_mcp.tools.blockchain import get_latest_block, get_balance


class FakeClient:
    def get_latest_block(self):
        return {"height": 123, "hash": "abc", "timestamp": "2025-01-01T00:00:00Z"}

    def get_balance(self, address: str):
        return "42"


def test_get_latest_block_ok():
    resp = get_latest_block(FakeClient())
    assert resp.ok and isinstance(resp.raw, dict)


def test_get_balance_ok():
    req = BalanceRequest(address="deadbeef")
    resp = get_balance(FakeClient(), req)
    assert resp.ok and resp.balance == "42"


