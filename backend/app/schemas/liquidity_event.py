from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class LiquidityEventCreate(BaseModel):
    token_address: str
    token_symbol: Optional[str] = None
    chain: str

    event_type: str

    amount_usd: Optional[float] = None
    pct_change: Optional[float] = None
    liquidity_before: Optional[float] = None
    liquidity_after: Optional[float] = None

    wallet_address: Optional[str] = None
    is_dev_wallet: bool = False
    is_suspicious: bool = False

    risk_score: float = 0.0

    tx_hash: Optional[str] = None
    timestamp: datetime


class LiquidityEventOut(BaseModel):
    id: int
    token_address: str
    token_symbol: Optional[str]
    chain: str

    event_type: str

    amount_usd: Optional[float]
    pct_change: Optional[float]
    liquidity_before: Optional[float]
    liquidity_after: Optional[float]

    wallet_address: Optional[str]
    is_dev_wallet: bool
    is_suspicious: bool

    risk_score: float

    tx_hash: Optional[str]
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
