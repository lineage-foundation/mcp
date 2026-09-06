import anyio


def test_server_import():
    # Ensure the server module loads and exposes app
    from lineage_mcp.server import app, mcp  # noqa: F401


def test_expected_tool_names():
    from lineage_mcp.server import mcp
    names = {t.name for t in anyio.run(mcp.list_tools)}
    expected = {
        "health", "version", "generate-seed-phrase", "generate-keypair",
        "get-entry-by-hash", "fetch-transactions",
        "get-block", "get-transaction", "get-address-balance", "get-supply", "get-latest-block",
        "list-blocks", "list-transactions", "list-block-transactions",
        "list-address-transactions", "search-items", "get-status",
    }
    assert names == expected
    removed = {"get-block-by-number", "get-transaction-by-hash", "get-total-supply",
               "get-issued-supply", "fetch-balance"}
    assert names.isdisjoint(removed)
