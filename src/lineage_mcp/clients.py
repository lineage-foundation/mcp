from __future__ import annotations

from lineage import get_default_config
from lineage.blockchain import BlockchainClient

from .config import AppConfig


def create_blockchain_client(config: AppConfig) -> BlockchainClient:
    # BlockchainClient requires a storage host; fall back to the SDK's public
    # defaults when the corresponding env vars are unset.
    defaults = get_default_config()
    return BlockchainClient(
        storage_host=config.storage_host or defaults["storageHost"],
        mempool_host=config.mempool_host or defaults["mempoolHost"],
        api_key=config.api_key,
    )
