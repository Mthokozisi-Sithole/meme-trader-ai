"""Add intelligence tables: wallets, wallet_transactions, behavioral_signals,
liquidity_events, holder_snapshots, token_timeseries

Revision ID: 0004
Revises: 43950320aec7
Create Date: 2026-03-28
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "43950320aec7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------ wallets
    op.create_table(
        "wallets",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("address", sa.String(100), unique=True, nullable=False, index=True),
        sa.Column("chain", sa.String(50), nullable=False, index=True),

        # Classification
        sa.Column("wallet_type", sa.String(30), nullable=False, server_default="unknown", index=True),
        sa.Column("label", sa.String(100), nullable=True),
        sa.Column("classification_confidence", sa.Float, server_default="0.0"),

        # Performance metrics
        sa.Column("total_txns", sa.Integer, server_default="0"),
        sa.Column("win_rate", sa.Float, nullable=True),
        sa.Column("avg_hold_hours", sa.Float, nullable=True),
        sa.Column("total_realized_pnl_usd", sa.Float, nullable=True),
        sa.Column("rug_exits", sa.Integer, server_default="0"),
        sa.Column("times_early_buyer", sa.Integer, server_default="0"),

        # Behavior flags
        sa.Column("is_dev_wallet", sa.Boolean, server_default="false"),
        sa.Column("is_bot", sa.Boolean, server_default="false"),
        sa.Column("is_coordinated", sa.Boolean, server_default="false"),
        sa.Column("flagged", sa.Boolean, server_default="false"),

        # Quality score
        sa.Column("quality_score", sa.Float, server_default="50.0"),

        # Raw behavior JSON
        sa.Column("behavior_data", sa.Text, nullable=True),

        sa.Column("first_seen", sa.DateTime, server_default=sa.func.now()),
        sa.Column("last_active", sa.DateTime, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -------------------------------------------------------- wallet_transactions
    op.create_table(
        "wallet_transactions",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("wallet_address", sa.String(100), nullable=False, index=True),
        sa.Column("token_address", sa.String(100), nullable=False, index=True),
        sa.Column("chain", sa.String(50), nullable=False, index=True),

        # Action: buy | sell | add_lp | remove_lp | transfer
        sa.Column("action", sa.String(20), nullable=False, index=True),

        sa.Column("amount_usd", sa.Float, nullable=True),
        sa.Column("token_amount", sa.Float, nullable=True),
        sa.Column("price_at_action", sa.Float, nullable=True),

        # Context flags
        sa.Column("is_first_buy", sa.Boolean, server_default="false"),
        sa.Column("is_dev_wallet", sa.Boolean, server_default="false"),
        sa.Column("is_smart_money", sa.Boolean, server_default="false"),
        sa.Column("is_sniper", sa.Boolean, server_default="false"),

        sa.Column("tx_hash", sa.String(200), nullable=True),
        sa.Column("block_number", sa.Integer, nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # -------------------------------------------------------- behavioral_signals
    op.create_table(
        "behavioral_signals",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("token_address", sa.String(100), nullable=False, index=True),
        sa.Column("token_symbol", sa.String(50), nullable=True, index=True),
        sa.Column("chain", sa.String(50), nullable=False, index=True),

        # Pattern type
        sa.Column("pattern_type", sa.String(50), nullable=False, index=True),

        # Human-readable signal label
        sa.Column("signal_label", sa.String(100), nullable=False),

        # Confidence 0-100
        sa.Column("confidence", sa.Float, nullable=False),

        # Severity: info | warning | alert | critical
        sa.Column("severity", sa.String(20), nullable=False, server_default="info", index=True),

        # JSON blobs
        sa.Column("supporting_metrics", sa.Text, nullable=True),
        sa.Column("contributing_factors", sa.Text, nullable=True),
        sa.Column("raw_data_snapshot", sa.Text, nullable=True),

        # Lifecycle
        sa.Column("is_active", sa.Boolean, server_default="true", index=True),
        sa.Column("resolved_at", sa.DateTime, nullable=True),
        sa.Column("expires_at", sa.DateTime, nullable=True),

        # Signal fusion score
        sa.Column("fusion_score", sa.Float, server_default="0.0"),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), index=True),
    )

    # --------------------------------------------------------- liquidity_events
    op.create_table(
        "liquidity_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("token_address", sa.String(100), nullable=False, index=True),
        sa.Column("token_symbol", sa.String(50), nullable=True),
        sa.Column("chain", sa.String(50), nullable=False, index=True),

        # Event type: add | remove | migrate | lock | unlock
        sa.Column("event_type", sa.String(20), nullable=False, index=True),

        sa.Column("amount_usd", sa.Float, nullable=True),
        sa.Column("pct_change", sa.Float, nullable=True),
        sa.Column("liquidity_before", sa.Float, nullable=True),
        sa.Column("liquidity_after", sa.Float, nullable=True),

        sa.Column("wallet_address", sa.String(100), nullable=True, index=True),
        sa.Column("is_dev_wallet", sa.Boolean, server_default="false"),
        sa.Column("is_suspicious", sa.Boolean, server_default="false"),

        # Risk score for this event (0-100)
        sa.Column("risk_score", sa.Float, server_default="0.0"),

        sa.Column("tx_hash", sa.String(200), nullable=True),
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --------------------------------------------------------- holder_snapshots
    op.create_table(
        "holder_snapshots",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("token_address", sa.String(100), nullable=False, index=True),
        sa.Column("token_symbol", sa.String(50), nullable=True),
        sa.Column("chain", sa.String(50), nullable=False, index=True),

        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),

        # Holder counts
        sa.Column("holder_count", sa.Integer, nullable=True),

        # Concentration metrics (percentage 0-100)
        sa.Column("top1_pct", sa.Float, nullable=True),
        sa.Column("top5_pct", sa.Float, nullable=True),
        sa.Column("top10_pct", sa.Float, nullable=True),
        sa.Column("top20_pct", sa.Float, nullable=True),

        # Classified wallet holdings
        sa.Column("dev_holdings_pct", sa.Float, nullable=True),
        sa.Column("smart_money_pct", sa.Float, nullable=True),
        sa.Column("sniper_pct", sa.Float, nullable=True),
        sa.Column("bot_pct", sa.Float, nullable=True),
        sa.Column("retail_pct", sa.Float, nullable=True),

        # Derived risk score (0-100)
        sa.Column("concentration_risk", sa.Float, server_default="0.0"),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    # --------------------------------------------------------- token_timeseries
    op.create_table(
        "token_timeseries",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("token_address", sa.String(100), nullable=False, index=True),
        sa.Column("token_symbol", sa.String(50), nullable=True),
        sa.Column("chain", sa.String(50), nullable=False, index=True),

        # Bucket timestamp (rounded to nearest minute)
        sa.Column("timestamp", sa.DateTime, nullable=False, index=True),

        # OHLCV
        sa.Column("price_open", sa.Float, nullable=True),
        sa.Column("price_high", sa.Float, nullable=True),
        sa.Column("price_low", sa.Float, nullable=True),
        sa.Column("price_close", sa.Float, nullable=True),
        sa.Column("volume_usd", sa.Float, nullable=True),

        # Market state
        sa.Column("liquidity_usd", sa.Float, nullable=True),
        sa.Column("market_cap", sa.Float, nullable=True),
        sa.Column("holder_count", sa.Integer, nullable=True),

        # Behavioral state at this moment
        sa.Column("buy_pressure_pct", sa.Float, nullable=True),
        sa.Column("buys", sa.Integer, nullable=True),
        sa.Column("sells", sa.Integer, nullable=True),

        # Detected behavioral state
        sa.Column("behavioral_state", sa.String(30), nullable=True),

        # Scores at this point in time (for backtesting)
        sa.Column("snipe_score", sa.Float, nullable=True),
        sa.Column("fusion_score", sa.Float, nullable=True),

        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),

        sa.UniqueConstraint("token_address", "chain", "timestamp", name="uq_timeseries_token_ts"),
    )


def downgrade() -> None:
    op.drop_table("token_timeseries")
    op.drop_table("holder_snapshots")
    op.drop_table("liquidity_events")
    op.drop_table("behavioral_signals")
    op.drop_table("wallet_transactions")
    op.drop_table("wallets")
