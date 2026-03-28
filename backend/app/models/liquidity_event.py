from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class LiquidityEvent(Base):
    __tablename__ = "liquidity_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_symbol: Mapped[str | None] = mapped_column(String(50))
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Event type: add | remove | migrate | lock | unlock
    event_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    amount_usd: Mapped[float | None] = mapped_column(Float)
    pct_change: Mapped[float | None] = mapped_column(Float)        # % change in liquidity
    liquidity_before: Mapped[float | None] = mapped_column(Float)
    liquidity_after: Mapped[float | None] = mapped_column(Float)

    wallet_address: Mapped[str | None] = mapped_column(String(100), index=True)
    is_dev_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    is_suspicious: Mapped[bool] = mapped_column(Boolean, default=False)

    # Risk score for this specific event (0-100)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)

    tx_hash: Mapped[str | None] = mapped_column(String(200))
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
