from datetime import datetime
from typing import Optional
from pydantic import BaseModel, computed_field


class WalletCreate(BaseModel):
    address: str
    chain: str
    wallet_type: str = "unknown"
    label: Optional[str] = None
    classification_confidence: float = 0.0

    total_txns: int = 0
    win_rate: Optional[float] = None
    avg_hold_hours: Optional[float] = None
    total_realized_pnl_usd: Optional[float] = None
    rug_exits: int = 0
    times_early_buyer: int = 0

    is_dev_wallet: bool = False
    is_bot: bool = False
    is_coordinated: bool = False
    flagged: bool = False

    quality_score: float = 50.0
    behavior_data: Optional[str] = None  # JSON string

    first_seen: Optional[datetime] = None
    last_active: Optional[datetime] = None


class WalletOut(BaseModel):
    id: int
    address: str
    chain: str
    wallet_type: str
    label: Optional[str]
    classification_confidence: float

    total_txns: int
    win_rate: Optional[float]
    avg_hold_hours: Optional[float]
    total_realized_pnl_usd: Optional[float]
    rug_exits: int
    times_early_buyer: int

    is_dev_wallet: bool
    is_bot: bool
    is_coordinated: bool
    flagged: bool

    quality_score: float
    behavior_data: Optional[str]

    first_seen: datetime
    last_active: datetime
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[misc]
    @property
    def type_label(self) -> str:
        """Human-readable label for the wallet type."""
        _labels: dict[str, str] = {
            "smart_money": "Smart Money",
            "dev": "Developer Wallet",
            "bot": "Bot",
            "whale": "Whale",
            "sniper": "Sniper",
            "dumper": "Dumper",
            "retail": "Retail",
            "unknown": "Unknown",
        }
        return _labels.get(self.wallet_type, self.wallet_type.replace("_", " ").title())

    model_config = {"from_attributes": True}


class WalletTransactionCreate(BaseModel):
    wallet_address: str
    token_address: str
    chain: str
    action: str

    amount_usd: Optional[float] = None
    token_amount: Optional[float] = None
    price_at_action: Optional[float] = None

    is_first_buy: bool = False
    is_dev_wallet: bool = False
    is_smart_money: bool = False
    is_sniper: bool = False

    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    timestamp: datetime


class WalletTransactionOut(BaseModel):
    id: int
    wallet_address: str
    token_address: str
    chain: str
    action: str

    amount_usd: Optional[float]
    token_amount: Optional[float]
    price_at_action: Optional[float]

    is_first_buy: bool
    is_dev_wallet: bool
    is_smart_money: bool
    is_sniper: bool

    tx_hash: Optional[str]
    block_number: Optional[int]
    timestamp: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
