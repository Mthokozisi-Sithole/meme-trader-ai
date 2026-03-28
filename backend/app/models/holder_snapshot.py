from datetime import datetime
from sqlalchemy import String, Float, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class HolderSnapshot(Base):
    __tablename__ = "holder_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_symbol: Mapped[str | None] = mapped_column(String(50))
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    # Holder counts
    holder_count: Mapped[int | None] = mapped_column(Integer)

    # Concentration metrics (percentage 0-100)
    top1_pct: Mapped[float | None] = mapped_column(Float)
    top5_pct: Mapped[float | None] = mapped_column(Float)
    top10_pct: Mapped[float | None] = mapped_column(Float)
    top20_pct: Mapped[float | None] = mapped_column(Float)

    # Classified wallet holdings
    dev_holdings_pct: Mapped[float | None] = mapped_column(Float)
    smart_money_pct: Mapped[float | None] = mapped_column(Float)
    sniper_pct: Mapped[float | None] = mapped_column(Float)
    bot_pct: Mapped[float | None] = mapped_column(Float)
    retail_pct: Mapped[float | None] = mapped_column(Float)

    # Derived risk score (0-100, higher = more concentrated = riskier)
    concentration_risk: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
