from datetime import datetime
from sqlalchemy import String, Float, Integer, Boolean, Text, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class BehavioralSignal(Base):
    __tablename__ = "behavioral_signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token_address: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    token_symbol: Mapped[str | None] = mapped_column(String(50), index=True)
    chain: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Pattern type: accumulation | pre_breakout | fake_breakout | liquidity_trap |
    #   momentum_ignition | volume_anomaly | dev_exit | rug_risk | smart_money_entry |
    #   coordinated_buy | wash_trading | holder_distribution_risk
    pattern_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Human-readable signal: "Early Momentum Detected" | "Smart Money Accumulation" | etc.
    signal_label: Mapped[str] = mapped_column(String(100), nullable=False)

    # Confidence 0-100
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    # Severity: info | warning | alert | critical
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="info", index=True)

    # JSON blobs
    supporting_metrics: Mapped[str | None] = mapped_column(Text)   # JSON: key metrics that support this signal
    contributing_factors: Mapped[str | None] = mapped_column(Text) # JSON: factor weights that contributed
    raw_data_snapshot: Mapped[str | None] = mapped_column(Text)    # JSON: token state when signal fired

    # Lifecycle
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime)

    # Signal fusion score (0-100) — combined score from all factors
    fusion_score: Mapped[float] = mapped_column(Float, default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
