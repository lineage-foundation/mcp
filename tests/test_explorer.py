import httpx
import pytest

from lineage_mcp.explorer import ExplorerClient, ExplorerError


def _client(handler):
    transport = httpx.MockTransport(handler)
    http = httpx.Client(base_url="https://explorer.test", transport=transport)
    return ExplorerClient(client=http)


def test_get_status_ok():
    def handler(request):
        assert request.url.path == "/api/v1/status"
        return httpx.Response(200, json={"network": "Lineage", "height": 7017})
    ex = _client(handler)
    assert ex.get_status()["height"] == 7017


def test_list_blocks_builds_query():
    seen = {}
    def handler(request):
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json={"data": [], "pagination": {}})
    ex = _client(handler)
    ex.list_blocks(limit=5, offset=10, order="asc")
    assert seen["path"] == "/api/v1/blocks"
    assert seen["params"] == {"limit": "5", "offset": "10", "order": "asc"}


def test_get_transaction_path_encoded():
    def handler(request):
        assert request.url.raw_path == b"/api/v1/transactions/abc%20def"
        return httpx.Response(200, json={"hash": "abc def"})
    ex = _client(handler)
    assert ex.get_transaction("abc def")["hash"] == "abc def"


def test_not_found_raises_with_status():
    def handler(request):
        return httpx.Response(404, json={"title": "Transaction not found", "detail": "no"})
    ex = _client(handler)
    with pytest.raises(ExplorerError) as e:
        ex.get_transaction("deadbeef")
    assert e.value.status == 404


def test_transport_error_raises_status_none():
    def handler(request):
        raise httpx.ConnectError("boom")
    ex = _client(handler)
    with pytest.raises(ExplorerError) as e:
        ex.get_status()
    assert e.value.status is None
