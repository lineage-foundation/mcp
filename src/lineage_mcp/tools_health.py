from __future__ import annotations

import time

from .__about__ import __version__


def health() -> dict:
    return {"ok": True, "time": int(time.time())}


def version() -> dict:
    return {"ok": True, "version": __version__}


