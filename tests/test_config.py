import importlib


def _fresh_config(monkeypatch, **env):
    for k in ("LINEAGE_EXPLORER_URL", "LINEAGE_EXPLORER_TIMEOUT_S"):
        monkeypatch.delenv(k, raising=False)
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    import lineage_mcp.config as config
    importlib.reload(config)
    return config.get_config()


def test_explorer_defaults(monkeypatch):
    cfg = _fresh_config(monkeypatch)
    assert cfg.explorer_url == "https://explorer.lineage.to"
    assert cfg.explorer_timeout_s == 10.0


def test_explorer_env_override(monkeypatch):
    cfg = _fresh_config(monkeypatch, LINEAGE_EXPLORER_URL="http://x:9/", LINEAGE_EXPLORER_TIMEOUT_S="3.5")
    assert cfg.explorer_url == "http://x:9/"
    assert cfg.explorer_timeout_s == 3.5
