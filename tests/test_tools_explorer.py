from lineage.interfaces import IResult

from lineage_mcp import tools_explorer as te
from lineage_mcp.explorer import ExplorerError


class FakeExplorer:
    """Records the last call and returns canned payloads or raises."""

    def __init__(self, payload=None, error=None):
        self._payload = payload
        self._error = error
        self.calls = []

    def _ret(self, name, **kw):
        self.calls.append((name, kw))
        if self._error is not None:
            raise self._error
        return self._payload

    def list_blocks(self, **kw): return self._ret("list_blocks", **kw)
    def list_transactions(self, **kw): return self._ret("list_transactions", **kw)
    def list_block_transactions(self, id): return self._ret("list_block_transactions", id=id)
    def list_address_transactions(self, address, **kw): return self._ret("list_address_transactions", address=address, **kw)
    def search_items(self, **kw): return self._ret("search_items", **kw)
    def get_status(self): return self._ret("get_status")
    def get_block(self, id): return self._ret("get_block", id=id)
    def get_transaction(self, tx_hash): return self._ret("get_transaction", tx_hash=tx_hash)
    def get_address(self, address): return self._ret("get_address", address=address)
    def get_supply(self): return self._ret("get_supply")


def test_list_blocks_ok():
    ex = FakeExplorer(payload={"data": [{"num": 1}], "pagination": {"total": 1}})
    resp = te.list_blocks(ex, limit=5)
    assert resp == {"ok": True, "source": "explorer", "data": [{"num": 1}], "pagination": {"total": 1}}
    assert ex.calls[0] == ("list_blocks", {"limit": 5, "offset": 0, "order": "desc"})


def test_get_status_ok_single_object():
    ex = FakeExplorer(payload={"network": "Lineage", "height": 7})
    resp = te.get_status(ex)
    assert resp == {"ok": True, "source": "explorer", "data": {"network": "Lineage", "height": 7}}


def test_search_items_requires_q_or_genesis():
    ex = FakeExplorer(payload={"data": []})
    resp = te.search_items(ex)
    assert resp["ok"] is False and "q" in resp["error"]
    assert ex.calls == []  # never hit the API


def test_search_items_with_q():
    ex = FakeExplorer(payload={"data": [{"genesisHash": "g"}], "pagination": {}})
    resp = te.search_items(ex, q="foo")
    assert resp["ok"] is True and resp["data"] == [{"genesisHash": "g"}]


def test_explorer_error_surfaces_status():
    ex = FakeExplorer(error=ExplorerError("not found", status=404))
    resp = te.list_transactions(ex)
    assert resp == {"ok": False, "error": "404 not found", "status": 404}


def _ok(payload):
    return lambda: IResult.ok(payload)


def _err(msg):
    return lambda: IResult.err(msg)


def test_get_transaction_verified_true():
    ex = FakeExplorer(payload={"hash": "h1", "blockHash": "b1"})
    resp = te.get_transaction(ex, _ok({"hash": "h1"}), "h1")
    assert resp["ok"] is True
    assert resp["source"] == "explorer"
    assert resp["verified"] is True
    assert resp["data"] == {"hash": "h1", "blockHash": "b1"}


def test_get_transaction_mismatch_false():
    ex = FakeExplorer(payload={"hash": "h1"})
    resp = te.get_transaction(ex, _ok({"hash": "DIFFERENT"}), "h1")
    assert resp["verified"] is False
    assert resp["verification"]["chain_value"] == "DIFFERENT"


def test_get_transaction_chain_down_unverified():
    ex = FakeExplorer(payload={"hash": "h1"})
    resp = te.get_transaction(ex, _err("node down"), "h1")
    assert resp["verified"] == "unverified"
    assert resp["source"] == "explorer"
    assert resp["data"] == {"hash": "h1"}


def test_verify_false_skips_chain():
    ex = FakeExplorer(payload={"hash": "h1"})
    called = {"n": 0}
    def sdk():
        called["n"] += 1
        return IResult.ok({"hash": "h1"})
    resp = te.get_transaction(ex, sdk, "h1", verify=False)
    assert resp["verified"] == "skipped"
    assert "verification" not in resp
    assert called["n"] == 0


def test_explorer_down_falls_back_to_chain():
    ex = FakeExplorer(error=ExplorerError("timeout", status=None))
    resp = te.get_transaction(ex, _ok({"hash": "h1", "onchain": True}), "h1")
    assert resp["ok"] is True
    assert resp["source"] == "chain"
    assert resp["verified"] is True
    assert resp["data"] == {"hash": "h1", "onchain": True}


def test_explorer_404_does_not_fall_back():
    ex = FakeExplorer(error=ExplorerError("not found", status=404))
    resp = te.get_transaction(ex, _ok({"hash": "h1"}), "h1")
    assert resp["ok"] is False
    assert resp["status"] == 404


def test_both_down_returns_error():
    ex = FakeExplorer(error=ExplorerError("timeout", status=None))
    resp = te.get_transaction(ex, _err("node down"), "h1")
    assert resp["ok"] is False
    assert "node down" in resp["error"]


def test_get_supply_verified_on_total():
    ex = FakeExplorer(payload={"total": "360360000000000000", "circulating": "9"})
    resp = te.get_supply(ex, _ok({"total": "360360000000000000"}))
    assert resp["verified"] is True
