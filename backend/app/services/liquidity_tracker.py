"""
Liquidity event risk scoring and manipulation detection.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LiquidityEventInput:
    event_type: str                         # add | remove | migrate | lock | unlock
    amount_usd: float
    pct_change: Optional[float]             # % change in total pool liquidity
    is_dev_wallet: bool
    wallet_address: str
    token_age_hours: Optional[float]
    current_liquidity_usd: float
    prev_liquidity_usd: float
    transaction_hash: str


@dataclass
class LiquidityRiskResult:
    risk_score: float           # 0-100
    is_suspicious: bool
    risk_flags: list[str]       # e.g. ["dev_remove_early", "large_remove", "rug_pattern"]
    severity: str               # info | warning | alert | critical
    description: str


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def assess_liquidity_event(event: LiquidityEventInput) -> LiquidityRiskResult:
    """
    Score a liquidity event for manipulation risk.

    Risk factors:
      dev_remove_early: dev wallet removes LP within 24h of launch → +50
      large_remove:     remove > 30% of pool → +30
      rapid_remove:     treated as multiple removes context → +20
      rug_pattern:      remove > 50% + dev + young token → score = 90, critical
      migration:        migrate from dev wallet → +25
      lp_lock:          reduce risk by -30 (positive signal)
      dev_add:          LP add from dev → -10 (slightly positive)

    Returns:
        LiquidityRiskResult with risk_score, flags, severity, and description.
    """
    risk_score = 0.0
    flags: list[str] = []
    description_parts: list[str] = []

    event_type = event.event_type.lower()
    token_age = event.token_age_hours or float("inf")
    pct_change = event.pct_change or 0.0

    # ---- LP LOCK (positive signal, reduce risk) ----
    if event_type == "lock":
        risk_score -= 30.0
        description_parts.append("LP locked — reduces rug risk.")

    # ---- LP ADD from dev (slightly positive) ----
    elif event_type == "add" and event.is_dev_wallet:
        risk_score -= 10.0
        description_parts.append("Dev wallet added liquidity.")

    # ---- REMOVAL EVENTS ----
    elif event_type == "remove":
        # rug_pattern: remove >50% + dev wallet + young token (<48h)
        if abs(pct_change) > 50.0 and event.is_dev_wallet and token_age < 48.0:
            risk_score = 90.0
            flags.append("rug_pattern")
            description_parts.append(
                f"RUG PATTERN: Dev removed {abs(pct_change):.0f}% of liquidity "
                f"from a {token_age:.0f}h-old token."
            )
        else:
            # dev_remove_early: dev wallet removes within 24h of launch
            if event.is_dev_wallet and token_age < 24.0:
                risk_score += 50.0
                flags.append("dev_remove_early")
                description_parts.append(
                    f"Dev wallet removed LP only {token_age:.1f}h after launch."
                )

            # large_remove: remove >30% of pool
            if abs(pct_change) > 30.0:
                risk_score += 30.0
                flags.append("large_remove")
                description_parts.append(
                    f"Large LP removal: {abs(pct_change):.0f}% of pool removed."
                )

    # ---- MIGRATION from dev wallet ----
    elif event_type == "migrate" and event.is_dev_wallet:
        risk_score += 25.0
        flags.append("suspicious_migration")
        description_parts.append("Dev wallet initiated pool migration — verify intent.")

    elif event_type == "migrate":
        risk_score += 10.0
        description_parts.append("Pool migration event detected.")

    # ---- UNLOCK ----
    elif event_type == "unlock":
        risk_score += 15.0
        flags.append("lp_unlock")
        description_parts.append("LP unlock event — monitor for subsequent removal.")

    # Clamp to [0, 100]
    risk_score = round(_clamp(risk_score), 2)

    # Determine severity
    if risk_score >= 80.0 or "rug_pattern" in flags:
        severity = "critical"
        is_suspicious = True
    elif risk_score >= 50.0:
        severity = "alert"
        is_suspicious = True
    elif risk_score >= 25.0:
        severity = "warning"
        is_suspicious = risk_score >= 30.0
    else:
        severity = "info"
        is_suspicious = False

    description = " ".join(description_parts) if description_parts else "Normal liquidity activity."

    return LiquidityRiskResult(
        risk_score=risk_score,
        is_suspicious=is_suspicious,
        risk_flags=flags,
        severity=severity,
        description=description,
    )
