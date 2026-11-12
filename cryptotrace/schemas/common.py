"""Common enumerations and value types for CryptoTrace schemas."""

from enum import Enum


class BlockchainType(str, Enum):
    """Supported blockchain ecosystems."""
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"


class ChainIdentifier(str, Enum):
    """Network-level chain identifiers."""
    BITCOIN_MAINNET = "btc-mainnet"
    BITCOIN_TESTNET = "btc-testnet"
    ETHEREUM_MAINNET = "eth-mainnet"
    ETHEREUM_SEPOLIA = "eth-sepolia"


class TransactionStatus(str, Enum):
    """Finality status of a blockchain transaction."""
    CONFIRMED = "confirmed"
    PENDING = "pending"
    FAILED = "failed"
    REORG_DROPPED = "reorg_dropped"


class NodeType(str, Enum):
    """Types of entities represented in the forensics graph."""
    WALLET = "wallet"
    TRANSACTION = "transaction"
    CONTRACT = "contract"
    SERVICE = "service"
    EXCHANGE = "exchange"
    MIXER = "mixer"


class EdgeType(str, Enum):
    """Classification of directed graph relationships."""
    CONFIRMED_TRANSFER = "confirmed_transfer"
    UTXO_INPUT = "utxo_input"
    UTXO_OUTPUT = "utxo_output"
    ERC20_TRANSFER = "erc20_transfer"
    CONTRACT_CALL = "contract_call"
    INTERNAL_TRACE = "internal_trace"
    # Heuristics - explicitly distinguished
    HEURISTIC_CO_SPEND = "heuristic_co_spend"
    HEURISTIC_CHANGE_OUTPUT = "heuristic_change_output"
    BRIDGE_CORRELATED = "bridge_correlated"


class TransferCategory(str, Enum):
    """Asset class or transfer category."""
    NATIVE = "native"
    ERC20 = "erc20"
    INTERNAL_TRACE = "internal_trace"
    UTXO_FLOW = "utxo_flow"
