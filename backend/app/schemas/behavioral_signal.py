import json
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, model_validator


class BehavioralSignalCreate(BaseModel):
    token_address: str
    token_symbol: Optional[str] = None
    chain: str

    pattern_type: str
    signal_label: str
    confidence: float
    severity: str = "info"

    supporting_metrics: Optional[str] = None   # JSON string
    contributing_factors: Optional[str] = None  # JSON string
    raw_data_snapshot: Optional[str] = None     # JSON string

    is_active: bool = True
    resolved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    fusion_score: float = 0.0


class BehavioralSignalOut(BaseModel):
    id: int
    token_address: str
    token_symbol: Optional[str]
    chain: str

    pattern_type: str
    signal_label: str
    confidence: float
    severity: str

    # Parsed JSON fields — exposed as dicts for API consumers
    supporting_metrics: Optional[dict[str, Any]] = None
    contributing_factors: Optional[dict[str, Any]] = None
    raw_data_snapshot: Optional[str]  # kept as raw string — may be large

    is_active: bool
    resolved_at: Optional[datetime]
    expires_at: Optional[datetime]

    fusion_score: float
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def _parse_json_fields(cls, values: Any) -> Any:
        """Parse JSON string columns into dicts before validation."""
        # Handle ORM objects as well as plain dicts
        if hasattr(values, "__dict__"):
            data: dict[str, Any] = {
                k: v for k, v in vars(values).items() if not k.startswith("_")
            }
        else:
            data = dict(values) if values else {}

        for field in ("supporting_metrics", "contributing_factors"):
            raw = data.get(field)
            if isinstance(raw, str):
                try:
                    data[field] = json.loads(raw)
                except (json.JSONDecodeError, ValueError):
                    data[field] = None

        return data

    model_config = {"from_attributes": True}
