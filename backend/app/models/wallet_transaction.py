from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    wallet_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Action: buy | sell | add_lp | remove_lp | transfer
    action: Mapped[str] = mapped_column(String(20), nullable=False, index=True)

    amount_usd: Mapped[float | None] = mapped_column(Float)
    token_amount: Mapped[float | None] = mapped_column(Float)
    price_at_action: Mapped[float | None] = mapped_column(Float)

    # Context flags
    is_first_buy: Mapped[bool] = mapped_column(Boolean, default=False)
    is_dev_wallet: Mapped[bool] = mapped_column(Boolean, default=False)
    is_smart_money: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sniper: Mapped[bool] = mapped_column(Boolean, default=False)

    tx_hash: Mapped[str | None] = mapped_column(String(200))
    block_number: Mapped[int | None] = mapped_column(Integer)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
