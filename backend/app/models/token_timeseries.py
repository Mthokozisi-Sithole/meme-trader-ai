from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TokenTimeseries(Base):
    __tablename__ = "token_timeseries"
    __table_args__ = (
        UniqueConstraint("token_address", "chain", "timestamp", name="uq_timeseries_token_ts"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_symbol: Mapped[str | None] = mapped_column(String(50))
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Bucket timestamp (rounded to nearest minute)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # OHLCV
    price_open: Mapped[float | None] = mapped_column(Float)
    price_high: Mapped[float | None] = mapped_column(Float)
    price_low: Mapped[float | None] = mapped_column(Float)
    price_close: Mapped[float | None] = mapped_column(Float)
    volume_usd: Mapped[float | None] = mapped_column(Float)

    # Market state
    liquidity_usd: Mapped[float | None] = mapped_column(Float)
    market_cap: Mapped[float | None] = mapped_column(Float)
    holder_count: Mapped[int | None] = mapped_column(Integer)

    # Behavioral state at this moment
    buy_pressure_pct: Mapped[float | None] = mapped_column(Float)
    buys: Mapped[int | None] = mapped_column(Integer)
    sells: Mapped[int | None] = mapped_column(Integer)

    # Detected behavioral state: accumulation | distribution | neutral | breakout | breakdown | consolidation
    behavioral_state: Mapped[str | None] = mapped_column(String(30))

    # Scores at this point in time (for backtesting)
    snipe_score: Mapped[float | None] = mapped_column(Float)
    fusion_score: Mapped[float | None] = mapped_column(Float)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
