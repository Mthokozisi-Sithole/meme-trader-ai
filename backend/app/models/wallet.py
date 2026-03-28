from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    address: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Classification: smart_money | dev | bot | whale | sniper | dumper | retail | unknown
    wallet_type: Mapped[str] = mapped_column(String(30), nullable=False, default="unknown", index=True)
    label: Mapped[str | None] = mapped_column(String(100))
    classification_confidence: Mapped[float] = mapped_column(Float, default=0.0)

    # Performance metrics
    total_txns: Mapped[int] = mapped_column(Integer, default=0)
    win_rate: Mapped[float | None] = mapped_column(Float)          # 0.0-1.0
    avg_hold_hours: Mapped[float | None] = mapped_column(Float)
    total_realized_pnl_usd: Mapped[float | None] = mapped_column(Float)
    rug_exits: Mapped[int] = mapped_column(Integer, default=0)     # times sold before rug
    times_early_buyer: Mapped[int] = mapped_column(Integer, default=0)

    # Behavior flags
    is_dev_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    is_coordinated: Mapped[bool] = mapped_column(Boolean, default=False)  # coordinated group activity
    flagged: Mapped[bool] = mapped_column(Boolean, default=False)

    # Wallet quality score (0-100)
    quality_score: Mapped[float] = mapped_column(Float, default=50.0)

    # Raw behavior data as JSON string
    behavior_data: Mapped[str | None] = mapped_column(Text)  # JSON

    first_seen: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
