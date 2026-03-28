"""
Signal fusion model — combines behavioral, volume, wallet, liquidity, holder signals.

Default weights (configurable):
  volume_behavior:     0.25
  wallet_quality:      0.25
  dev_behavior:        0.20
  liquidity_health:    0.20
  holder_distribution: 0.10
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FusionWeights:
    volume_behavior: float = 0.25
    wallet_quality: float = 0.25
    dev_behavior: float = 0.20
    liquidity_health: float = 0.20
    holder_distribution: float = 0.10

    def validate(self) -> None:
        total = (
            self.volume_behavior
            + self.wallet_quality
            + self.dev_behavior
            + self.liquidity_health
            + self.holder_distribution
        )
        assert abs(total - 1.0) < 0.001, f"Weights must sum to 1.0, got {total}"


@dataclass
class FusionInput:
    # volume_behavior: 0-100 (from pattern_detector: anomaly → lower, healthy → higher)
    volume_score: float
    # wallet_quality: 0-100 (avg quality of wallets active in last 30min)
    wallet_quality_score: float
    # dev_behavior: 0-100 (100=dev holding + lp locked, 0=dev sold/rug risk)
    dev_behavior_score: float
    # liquidity_health: 0-100 (deep, stable liquidity → high)
    liquidity_score: float
    # holder_distribution: 0-100 (many holders, low concentration → high)
    holder_score: float
    # Optional overrides for specific risk flags
    has_rug_signal: bool = False
    has_wash_trading: bool = False
    has_dev_exit: bool = False


@dataclass
class FusionResult:
    fusion_score: float         # 0-100
    band: str                   # Strong Buy | Watch | Risky | Avoid
    component_scores: dict      # pre-adjustment scores per component
    risk_flags: list[str]       # active risk flags
    confidence: float           # 0-100 (based on data completeness)
    recommendation: str         # actionable recommendation string


_DEFAULT_WEIGHTS = FusionWeights()


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _score_to_band(score: float) -> str:
    if score >= 80.0:
        return "Strong Buy"
    if score >= 60.0:
        return "Watch"
    if score >= 40.0:
        return "Risky"
    return "Avoid"


def compute_fusion(
    inp: FusionInput,
    weights: FusionWeights | None = None,
) -> FusionResult:
    """
    Compute a weighted fusion score from multiple signal components.

    Risk override logic applied before final scoring:
      - has_rug_signal:   cap fusion_score at 20, add RUG_RISK flag
      - has_wash_trading: subtract 20 from volume component, add WASH_TRADING flag
      - has_dev_exit:     subtract 30 from dev component, add DEV_EXIT flag

    Args:
        inp:     Input signal scores and risk flags.
        weights: Optional custom FusionWeights (must sum to 1.0).

    Returns:
        FusionResult with score, band, component breakdown, flags, and recommendation.
    """
    w = weights or _DEFAULT_WEIGHTS
    w.validate()

    risk_flags: list[str] = []

    # Apply component-level risk adjustments before weighted sum
    volume_score = inp.volume_score
    dev_score = inp.dev_behavior_score

    if inp.has_wash_trading:
        volume_score = _clamp(volume_score - 20.0)
        risk_flags.append("WASH_TRADING")

    if inp.has_dev_exit:
        dev_score = _clamp(dev_score - 30.0)
        risk_flags.append("DEV_EXIT")

    # Clamp all component inputs to [0, 100]
    volume_score = _clamp(volume_score)
    wallet_score = _clamp(inp.wallet_quality_score)
    dev_score = _clamp(dev_score)
    liquidity_score = _clamp(inp.liquidity_score)
    holder_score = _clamp(inp.holder_score)

    component_scores = {
        "volume_behavior": round(volume_score, 2),
        "wallet_quality": round(wallet_score, 2),
        "dev_behavior": round(dev_score, 2),
        "liquidity_health": round(liquidity_score, 2),
        "holder_distribution": round(holder_score, 2),
    }

    # Weighted sum
    fusion_score = (
        w.volume_behavior * volume_score
        + w.wallet_quality * wallet_score
        + w.dev_behavior * dev_score
        + w.liquidity_health * liquidity_score
        + w.holder_distribution * holder_score
    )
    fusion_score = _clamp(fusion_score)

    # Rug signal: hard cap at 20 regardless of component scores
    if inp.has_rug_signal:
        fusion_score = min(fusion_score, 20.0)
        risk_flags.append("RUG_RISK")

    fusion_score = round(fusion_score, 2)

    # Confidence: based on data completeness (all inputs non-zero = full confidence)
    non_zero = sum(
        1 for s in [
            inp.volume_score,
            inp.wallet_quality_score,
            inp.dev_behavior_score,
            inp.liquidity_score,
            inp.holder_score,
        ]
        if s > 0
    )
    confidence = round(_clamp(non_zero / 5.0 * 100.0), 2)

    band = _score_to_band(fusion_score)

    # Recommendation
    has_critical_flag = inp.has_rug_signal or inp.has_wash_trading
    if fusion_score >= 75.0 and not risk_flags:
        recommendation = "Early entry opportunity — strong confluence"
    elif fusion_score >= 60.0 and not has_critical_flag:
        recommendation = "Monitor for entry — building momentum"
    elif fusion_score >= 40.0:
        recommendation = "High risk — trade only with tight SL"
    else:
        recommendation = "Avoid — adverse risk profile"

    return FusionResult(
        fusion_score=fusion_score,
        band=band,
        component_scores=component_scores,
        risk_flags=risk_flags,
        confidence=confidence,
        recommendation=recommendation,
    )
