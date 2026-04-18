from dataclasses import dataclass

from lineage.blockchain import BlockchainClient
from lineage.wallet import Wallet
from .config import AppConfig

@dataclass
class ServerContext:
    """
    Holds initialized shared dependencies like clients and configurations.
    Injected into tools to keep them pure and easily testable.
    """
    config: AppConfig
    blockchain_client: BlockchainClient
    wallet: Wallet
