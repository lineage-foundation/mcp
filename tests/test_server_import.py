def test_server_import():
    # Ensure the server module loads and exposes app
    from lineage_mcp.server import app, mcp  # noqa: F401


