from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


# Load from .env in local/dev; noop if file is absent
load_dotenv()


@dataclass(frozen=True)
class AppConfig:
    lineage_passphrase: str
    storage_host: Optional[str]
    mempool_host: Optional[str]
    valence_host: Optional[str]
    api_key: Optional[str]
    seed_phrase: Optional[str]
    explorer_url: str
    explorer_timeout_s: float
    log_level: str


def get_config() -> AppConfig:
    return AppConfig(
        lineage_passphrase=os.environ.get("LINEAGE_PASSPHRASE", ""),
        storage_host=os.environ.get("LINEAGE_STORAGE_HOST"),
        mempool_host=os.environ.get("LINEAGE_MEMPOOL_HOST"),
        valence_host=os.environ.get("LINEAGE_VALENCE_HOST"),
        api_key=os.environ.get("LINEAGE_API_KEY"),
        seed_phrase=os.environ.get("LINEAGE_SEED_PHRASE"),
        explorer_url=os.environ.get("LINEAGE_EXPLORER_URL", "https://explorer.lineage.to"),
        explorer_timeout_s=float(os.environ.get("LINEAGE_EXPLORER_TIMEOUT_S", "10")),
        log_level=os.environ.get("LOG_LEVEL", "INFO"),
    )
