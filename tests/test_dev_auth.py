import anyio

from lineage_mcp.server import _cors_wrapper


async def _inner_app(scope, receive, send):
    # Stand-in for the real MCP app: records that it was reached.
    await send({"type": "http.response.start", "status": 200, "headers": []})
    await send({"type": "http.response.body", "body": b"inner-app-reached"})


def _scope(method="POST", path="/mcp", headers=None):
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": headers or [],
    }


async def _receive():
    return {"type": "http.request", "body": b"", "more_body": False}


def _run(scope):
    events = []

    async def send(event):
        events.append(event)

    async def go():
        app = _cors_wrapper(_inner_app)
        await app(scope, _receive, send)

    anyio.run(go)
    return events


def _status(events):
    for event in events:
        if event.get("type") == "http.response.start":
            return event["status"]
    return None


def _reached_inner(events):
    for event in events:
        if event.get("type") == "http.response.body":
            return event.get("body") == b"inner-app-reached"
    return False


def test_dev_auth_missing_header_rejected(monkeypatch):
    monkeypatch.setenv("MCP_DEV_AUTH_TOKEN", "secret-token")
    events = _run(_scope())
    assert _status(events) == 401
    assert not _reached_inner(events)


def test_dev_auth_correct_bearer_token_passes(monkeypatch):
    monkeypatch.setenv("MCP_DEV_AUTH_TOKEN", "secret-token")
    events = _run(_scope(headers=[
        (b"authorization", b"Bearer secret-token"),
        (b"accept", b"text/event-stream"),
    ]))
    assert _status(events) != 401
    assert _reached_inner(events)


def test_dev_auth_wrong_bearer_token_rejected(monkeypatch):
    monkeypatch.setenv("MCP_DEV_AUTH_TOKEN", "secret-token")
    events = _run(_scope(headers=[(b"authorization", b"Bearer wrong-token")]))
    assert _status(events) == 401
    assert not _reached_inner(events)


def test_dev_auth_options_preflight_exempt(monkeypatch):
    monkeypatch.setenv("MCP_DEV_AUTH_TOKEN", "secret-token")
    events = _run(_scope(method="OPTIONS"))
    assert _status(events) == 204
    assert not _reached_inner(events)


def test_dev_auth_unset_no_auth_required(monkeypatch):
    monkeypatch.delenv("MCP_DEV_AUTH_TOKEN", raising=False)
    events = _run(_scope(headers=[(b"accept", b"text/event-stream")]))
    assert _status(events) != 401
    assert _reached_inner(events)
