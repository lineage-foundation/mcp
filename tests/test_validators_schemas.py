import pytest

from lineage_mcp.utils import ensure_non_empty, ensure_hex
from lineage_mcp.schemas import BalanceRequest


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


def test_balance_request_validation():
    req = BalanceRequest(address="deadbeef")
    assert req.address == "deadbeef"


