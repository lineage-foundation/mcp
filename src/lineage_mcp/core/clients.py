from __future__ import annotations


from lineage.blockchain import BlockchainClient

from .config import AppConfig


def create_blockchain_client(config: AppConfig) -> BlockchainClient:
    return BlockchainClient(
        storage_host=config.storage_host,
        mempool_host=config.mempool_host,
    )
