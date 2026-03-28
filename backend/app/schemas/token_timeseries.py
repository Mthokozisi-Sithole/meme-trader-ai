from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TimeseriesCreate(BaseModel):
    token_address: str
    token_symbol: Optional[str] = None
    chain: str

    timestamp: datetime

    price_open: Optional[float] = None
    price_high: Optional[float] = None
    price_low: Optional[float] = None
    price_close: Optional[float] = None
    volume_usd: Optional[float] = None

    liquidity_usd: Optional[float] = None
    market_cap: Optional[float] = None
    holder_count: Optional[int] = None

    buy_pressure_pct: Optional[float] = None
    buys: Optional[int] = None
    sells: Optional[int] = None

    behavioral_state: Optional[str] = None

    snipe_score: Optional[float] = None
    fusion_score: Optional[float] = None


class TimeseriesOut(BaseModel):
    id: int
    token_address: str
    token_symbol: Optional[str]
    chain: str

    timestamp: datetime

    price_open: Optional[float]
    price_high: Optional[float]
    price_low: Optional[float]
    price_close: Optional[float]
    volume_usd: Optional[float]

    liquidity_usd: Optional[float]
    market_cap: Optional[float]
    holder_count: Optional[int]

    buy_pressure_pct: Optional[float]
    buys: Optional[int]
    sells: Optional[int]

    behavioral_state: Optional[str]

    snipe_score: Optional[float]
    fusion_score: Optional[float]

    created_at: datetime

    model_config = {"from_attributes": True}
