from __future__ import annotations

import re


_HEX_RE = re.compile(r"^[0-9a-fA-F]+$")


def ensure_non_empty(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    return value


def ensure_hex(value: str, name: str) -> str:
    ensure_non_empty(value, name)
    if not _HEX_RE.match(value):
        raise ValueError(f"{name} must be hex-encoded")
    return value


