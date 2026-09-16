from lineage.interfaces import IResult

from lineage_mcp.tools_blockchain import get_latest_block, get_total_supply


class FakeClient:
    """Stand-in for lineage.BlockchainClient returning SDK-shaped IResults."""

    def __init__(self, *, ok=True):
        self._ok = ok

    def get_latest_block(self):
        if not self._ok:
            return IResult.err("node unreachable")
        return IResult.ok({"content": {"block": {"header": {"b_num": 123}}}})

    def get_total_supply(self):
        # The SDK may return a bare scalar; the tool wraps it into a dict.
        return IResult.ok(1000000)


def test_get_latest_block_passes_sdk_payload_through():
    resp = get_latest_block(FakeClient())
    assert resp == {"content": {"block": {"header": {"b_num": 123}}}}


def test_scalar_payload_is_wrapped():
    resp = get_total_supply(FakeClient())
    assert resp == {"value": 1000000}


def test_error_result_surfaces_sdk_message():
    resp = get_latest_block(FakeClient(ok=False))
    assert resp == {"ok": False, "error": "node unreachable"}
