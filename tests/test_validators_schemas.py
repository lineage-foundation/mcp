import pytest

from lineage_mcp.validators import ensure_non_empty, ensure_hex


def test_ensure_non_empty_ok():
    assert ensure_non_empty("abc", "name") == "abc"


def test_ensure_non_empty_fail():
    with pytest.raises(ValueError):
        ensure_non_empty("", "name")


def test_ensure_hex_ok():
    assert ensure_hex("deadbeef", "hex") == "deadbeef"


def test_ensure_hex_fail():
    with pytest.raises(ValueError):
        ensure_hex("zz", "hex")


