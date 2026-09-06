from lineage.interfaces import IResult

from lineage_mcp.verify import verify_against_chain, deep_get


def _cmp_hash(explorer_obj, chain_payload):
    cv = deep_get(chain_payload, "hash")
    return cv == explorer_obj.get("hash"), cv


def test_match():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.ok({"hash": "h1"}), _cmp_hash)
    assert verified is True
    assert v == {"method": "sdk", "matched": True, "chain_value": "h1", "note": None}


def test_mismatch():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.ok({"hash": "OTHER"}), _cmp_hash)
    assert verified is False
    assert v["matched"] is False and v["chain_value"] == "OTHER"


def test_chain_error_is_unverified():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.err("node down"), _cmp_hash)
    assert verified == "unverified"
    assert v["matched"] is None and "node down" in v["note"]


def test_chain_raises_is_unverified():
    obj = {"hash": "h1"}
    def boom():
        raise RuntimeError("kaboom")
    verified, v = verify_against_chain(obj, boom, _cmp_hash)
    assert verified == "unverified"
    assert "kaboom" in v["note"]


def _raise(*_):
    raise RuntimeError("cmp boom")


def test_compare_error_is_unverified():
    verified, v = verify_against_chain({"hash": "h1"}, lambda: IResult.ok({"hash": "h1"}), _raise)
    assert verified == "unverified"
    assert "cmp boom" in v["note"]


def _cmp_absent(_explorer_obj, _chain_payload):
    return None, None


def test_field_absent_on_chain_is_unverified():
    obj = {"hash": "h1"}
    verified, v = verify_against_chain(obj, lambda: IResult.ok({}), _cmp_absent)
    assert verified == "unverified"
    assert v["matched"] is None
    assert v["chain_value"] is None
    assert v["note"] == "chain payload had no comparable field"


def test_deep_get_nested():
    assert deep_get({"a": {"b": {"hash": "x"}}}, "hash") == "x"
    assert deep_get({"data": [{"num": 5}]}, "num") == 5
    assert deep_get({"a": 1}, "missing") is None
