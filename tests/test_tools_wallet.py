from lineage_mcp.tools_wallet import generate_seed_phrase, generate_keypair


def test_generate_seed_phrase():
    resp = generate_seed_phrase()
    assert resp["ok"] is True
    assert len(resp["seedPhrase"].split()) >= 12


def test_generate_keypair_random():
    resp = generate_keypair()
    assert resp["ok"] is True
    # address is a hex string, publicKey is hex-encoded from bytes
    assert isinstance(resp["address"], str) and resp["address"]
    assert isinstance(resp["publicKey"], str) and resp["publicKey"]


def test_generate_keypair_from_seed_is_deterministic():
    resp = generate_seed_phrase()
    seed = resp["seedPhrase"]
    a = generate_keypair(seed_phrase=seed)
    b = generate_keypair(seed_phrase=seed)
    assert a["address"] == b["address"]
