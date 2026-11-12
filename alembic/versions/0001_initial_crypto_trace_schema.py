"""Initial CryptoTrace schema migrations

Revision ID: 0001_initial_crypto_trace_schema
Revises: 
Create Date: 2026-11-12 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001_initial_crypto_trace_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. investigations
    op.create_table(
        "investigations",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("blockchain", sa.String(length=50), nullable=False),
        sa.Column("target_address", sa.String(length=128), nullable=False),
        sa.Column("max_hops", sa.Integer(), nullable=False, server_default="2"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="created"),
        sa.Column("total_transactions_ingested", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_nodes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_edges", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_investigation_blockchain_target", "investigations", ["blockchain", "target_address"])
    op.create_index("idx_investigation_status", "investigations", ["status"])

    # 2. wallets
    op.create_table(
        "wallets",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("address", sa.String(length=128), nullable=False),
        sa.Column("blockchain", sa.String(length=50), nullable=False),
        sa.Column("chain_id", sa.String(length=50), nullable=False),
        sa.Column("node_type", sa.String(length=50), nullable=False, server_default="wallet"),
        sa.Column("balance_native", sa.Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        sa.Column("total_received", sa.Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        sa.Column("total_sent", sa.Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        sa.Column("transaction_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_seen_timestamp", sa.Integer(), nullable=True),
        sa.Column("last_seen_timestamp", sa.Integer(), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_wallet_unique_chain_address", "wallets", ["blockchain", "address"], unique=True)
    op.create_index("idx_wallet_chain_type", "wallets", ["blockchain", "node_type"])

    # 3. transactions
    op.create_table(
        "transactions",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), sa.ForeignKey("investigations.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chain_id", sa.String(length=50), nullable=False),
        sa.Column("blockchain", sa.String(length=50), nullable=False),
        sa.Column("tx_hash", sa.String(length=128), nullable=False),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("block_hash", sa.String(length=128), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sender_references", sa.JSON(), nullable=False),
        sa.Column("recipient_references", sa.JSON(), nullable=False),
        sa.Column("asset_symbol", sa.String(length=50), nullable=False, server_default="NATIVE"),
        sa.Column("contract_address", sa.String(length=128), nullable=True),
        sa.Column("amount", sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column("fee", sa.Numeric(precision=38, scale=18), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="confirmed"),
        sa.Column("confirmations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("from_address", sa.String(length=128), nullable=True),
        sa.Column("to_address", sa.String(length=128), nullable=True),
        sa.Column("gas_used", sa.Integer(), nullable=True),
        sa.Column("gas_price_gwei", sa.Numeric(precision=38, scale=9), nullable=True),
        sa.Column("nonce", sa.Integer(), nullable=True),
        sa.Column("input_data", sa.Text(), nullable=True),
        sa.Column("vsize", sa.Integer(), nullable=True),
        sa.Column("locktime", sa.Integer(), nullable=True),
        sa.Column("raw_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("is_fixture", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_tx_unique_chain_hash", "transactions", ["blockchain", "tx_hash"], unique=True)
    op.create_index("idx_tx_block_timestamp", "transactions", ["blockchain", "block_number", "timestamp"])
    op.create_index("idx_tx_eth_addresses", "transactions", ["from_address", "to_address"])

    # 4. utxos
    op.create_table(
        "utxos",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("transaction_id", sa.String(length=36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tx_hash", sa.String(length=128), nullable=False),
        sa.Column("vout", sa.Integer(), nullable=False),
        sa.Column("address", sa.String(length=128), nullable=True),
        sa.Column("amount_sats", sa.Integer(), nullable=False),
        sa.Column("amount_btc", sa.Numeric(precision=38, scale=8), nullable=False),
        sa.Column("script_pubkey", sa.Text(), nullable=True),
        sa.Column("script_type", sa.String(length=50), nullable=True),
        sa.Column("is_spent", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("spending_tx_hash", sa.String(length=128), nullable=True),
        sa.Column("prev_tx_hash", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_utxo_tx_vout", "utxos", ["tx_hash", "vout"], unique=True)
    op.create_index("idx_utxo_address_spent", "utxos", ["address", "is_spent"])

    # 5. token_transfers
    op.create_table(
        "token_transfers",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("transaction_id", sa.String(length=36), sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("transaction_hash", sa.String(length=128), nullable=False),
        sa.Column("token_address", sa.String(length=128), nullable=False),
        sa.Column("token_symbol", sa.String(length=50), nullable=False),
        sa.Column("token_name", sa.String(length=100), nullable=True),
        sa.Column("token_decimals", sa.Integer(), nullable=False, server_default="18"),
        sa.Column("from_address", sa.String(length=128), nullable=False),
        sa.Column("to_address", sa.String(length=128), nullable=False),
        sa.Column("raw_value", sa.String(length=78), nullable=False),
        sa.Column("amount", sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column("log_index", sa.Integer(), nullable=True),
        sa.Column("block_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_tokentx_parties", "token_transfers", ["from_address", "to_address"])
    op.create_index("idx_tokentx_token_contract", "token_transfers", ["token_address", "token_symbol"])

    # 6. graph_nodes
    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("node_id", sa.String(length=128), nullable=False),
        sa.Column("node_type", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=128), nullable=False),
        sa.Column("blockchain", sa.String(length=50), nullable=False),
        sa.Column("chain_id", sa.String(length=50), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_graph_node_inv_id", "graph_nodes", ["investigation_id", "node_id"], unique=True)

    # 7. graph_edges
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.String(length=128), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=False),
        sa.Column("edge_type", sa.String(length=50), nullable=False),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_heuristic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("amount", sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column("asset_symbol", sa.String(length=50), nullable=False, server_default="NATIVE"),
        sa.Column("tx_hash", sa.String(length=128), nullable=False),
        sa.Column("evidence_reference", sa.String(length=200), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_graph_edge_lookup", "graph_edges", ["investigation_id", "source_id", "target_id"])
    op.create_index("idx_graph_edge_tx", "graph_edges", ["tx_hash"])

    # 8. investigation_paths
    op.create_table(
        "investigation_paths",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("investigation_id", sa.String(length=36), sa.ForeignKey("investigations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("path_nodes", sa.JSON(), nullable=False),
        sa.Column("hop_count", sa.Integer(), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=38, scale=18), nullable=False),
        sa.Column("summary_info", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_path_investigation_hops", "investigation_paths", ["investigation_id", "hop_count"])

    # 9. data_provenance
    op.create_table(
        "data_provenance",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("record_type", sa.String(length=50), nullable=False),
        sa.Column("record_identifier", sa.String(length=128), nullable=False),
        sa.Column("provider_name", sa.String(length=100), nullable=False),
        sa.Column("provider_endpoint", sa.String(length=255), nullable=True),
        sa.Column("retrieved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_fixture", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("raw_payload_hash", sa.String(length=64), nullable=False),
        sa.Column("response_latency_ms", sa.Float(), nullable=True),
        sa.Column("provider_metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("idx_prov_record_ident", "data_provenance", ["record_type", "record_identifier"])
    op.create_index("idx_prov_provider_time", "data_provenance", ["provider_name", "retrieved_at"])


def downgrade() -> None:
    op.drop_table("data_provenance")
    op.drop_table("investigation_paths")
    op.drop_table("graph_edges")
    op.drop_table("graph_nodes")
    op.drop_table("token_transfers")
    op.drop_table("utxos")
    op.drop_table("transactions")
    op.drop_table("wallets")
    op.drop_table("investigations")
