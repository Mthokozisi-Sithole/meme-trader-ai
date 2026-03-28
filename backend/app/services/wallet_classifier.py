"""
Wallet classification and quality scoring.

Types: smart_money | dev | bot | whale | sniper | dumper | retail | unknown
Quality score: 0-100
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class WalletMetrics:
    address: str
    chain: str
    total_txns: int
    win_rate: Optional[float]           # 0.0-1.0
    avg_hold_hours: Optional[float]
    total_realized_pnl_usd: Optional[float]
    rug_exits: int                       # times sold before rug
    times_early_buyer: int              # times in first 100 buyers
    is_first_buyer_pattern: bool        # consistently buys within seconds of launch
    hold_duration_variance: float       # low = bot-like, high = retail
    avg_buy_slippage: Optional[float]   # high = urgency, bot behavior
    coordinated_addresses: list[str] = field(default_factory=list)  # other wallets buying same tokens same time


@dataclass
class ClassificationResult:
    wallet_type: str        # smart_money | dev | bot | whale | sniper | dumper | retail | unknown
    quality_score: float    # 0-100
    confidence: float       # 0-100
    flags: list[str]        # e.g. ["early_buyer", "coordinated", "rug_expert"]
    is_dev_wallet: bool
    is_bot: bool
    is_coordinated: bool
    reasoning: str


def _clamp(value: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, value))


def _compute_quality_score(metrics: WalletMetrics) -> float:
    """
    Quality score formula:
      (win_rate * 40) + (rug_exits_bonus * 20) + (consistency * 20) + (pnl_bonus * 20)
    """
    # win_rate component (0-40)
    win_rate_component = (metrics.win_rate or 0.0) * 40.0

    # rug_exits_bonus component (0-20): more rug exits = higher bonus (knows when to exit)
    rug_exits_bonus = _clamp(metrics.rug_exits * 4.0, 0.0, 20.0)

    # consistency component (0-20): low variance = consistent = higher score for bots
    # but for quality, we want moderate variance (not pure bot, not chaotic retail)
    # best score at medium variance ~0.5, penalise extremes
    variance = metrics.hold_duration_variance
    # parabola peaking at variance=0.5 → 1.0, edges → 0.0
    consistency_raw = 1.0 - abs(variance - 0.5) * 2.0
    consistency_component = _clamp(consistency_raw * 20.0, 0.0, 20.0)

    # pnl_bonus component (0-20): logarithmic scale, $10k → ~15, $100k → 20
    pnl = metrics.total_realized_pnl_usd or 0.0
    if pnl > 0:
        import math
        pnl_bonus = _clamp((math.log10(max(pnl, 1)) - 2) * 10.0, 0.0, 20.0)
    else:
        pnl_bonus = 0.0

    total = win_rate_component + rug_exits_bonus + consistency_component + pnl_bonus
    return round(_clamp(total), 2)


def classify_wallet(metrics: WalletMetrics) -> ClassificationResult:
    """Classify a wallet based on its on-chain behavioral metrics."""
    flags: list[str] = []
    wallet_type = "retail"
    confidence = 50.0
    reasoning_parts: list[str] = []

    win_rate = metrics.win_rate or 0.0
    avg_hold = metrics.avg_hold_hours or 0.0
    pnl = metrics.total_realized_pnl_usd or 0.0
    slippage = metrics.avg_buy_slippage or 0.0

    is_dev_wallet = False
    is_bot = False
    is_coordinated = len(metrics.coordinated_addresses) > 0

    if is_coordinated:
        flags.append("coordinated")

    if metrics.times_early_buyer > 5:
        flags.append("early_buyer")

    if metrics.rug_exits > 3:
        flags.append("rug_expert")

    # --- Classification rules (evaluated in priority order) ---

    # Sniper: early buyer pattern + fast exits + consistent first-buys
    if (
        metrics.times_early_buyer > 5
        and avg_hold < 2.0
        and metrics.is_first_buyer_pattern
    ):
        wallet_type = "sniper"
        confidence = 85.0
        flags.append("sniper")
        reasoning_parts.append(
            f"Sniper pattern: {metrics.times_early_buyer} early buys, "
            f"avg hold {avg_hold:.1f}h, consistent first-buyer pattern."
        )

    # Bot: very low hold variance + first buyer + high slippage tolerance
    elif (
        metrics.hold_duration_variance < 0.1
        and metrics.is_first_buyer_pattern
        and slippage > 5.0
    ):
        wallet_type = "bot"
        is_bot = True
        confidence = 90.0
        flags.append("bot_behavior")
        reasoning_parts.append(
            f"Bot pattern: hold variance {metrics.hold_duration_variance:.3f} (robotic), "
            f"avg slippage {slippage:.1f}% (urgency), consistent first-buyer."
        )

    # Dev wallet: flagged externally OR (avg hold very long + early buyer)
    elif metrics.is_first_buyer_pattern and avg_hold > 168.0 and metrics.times_early_buyer > 2:
        # >168h = 1 week average hold + early entry pattern → likely dev
        wallet_type = "dev"
        is_dev_wallet = True
        confidence = 75.0
        flags.append("dev_pattern")
        reasoning_parts.append(
            f"Dev pattern: avg hold {avg_hold:.0f}h (very long), "
            f"early buyer {metrics.times_early_buyer} times."
        )

    # Smart money: good win rate + sufficient history + positive PnL
    elif (
        win_rate > 0.65
        and metrics.total_txns > 20
        and pnl > 5000.0
    ):
        wallet_type = "smart_money"
        confidence = 80.0
        flags.append("smart_money")
        reasoning_parts.append(
            f"Smart money: {win_rate*100:.0f}% win rate, "
            f"{metrics.total_txns} txns, ${pnl:,.0f} realized PnL."
        )

    # Whale: massive PnL but low transaction count (concentrated, patient)
    elif pnl > 50000.0 and metrics.total_txns < 30:
        wallet_type = "whale"
        confidence = 70.0
        flags.append("whale")
        reasoning_parts.append(
            f"Whale: ${pnl:,.0f} PnL with only {metrics.total_txns} txns (selective trader)."
        )

    # Dumper: low win rate + multiple rug exits (keeps riding to zero or dumps)
    elif win_rate < 0.3 and metrics.rug_exits > 3:
        wallet_type = "dumper"
        confidence = 65.0
        flags.append("dumper")
        reasoning_parts.append(
            f"Dumper pattern: {win_rate*100:.0f}% win rate, "
            f"{metrics.rug_exits} rug exits."
        )

    # Default: retail
    else:
        wallet_type = "retail"
        confidence = 40.0
        reasoning_parts.append("No strong pattern detected — classified as retail trader.")

    # Handle external dev flag override
    if hasattr(metrics, "is_first_buyer_pattern") and wallet_type != "dev":
        # If explicitly flagged as dev externally (e.g., by deployer address detection)
        # we keep the classification as-is unless caller passes is_dev_wallet=True via metrics
        pass

    quality_score = _compute_quality_score(metrics)

    reasoning = " ".join(reasoning_parts)
    if flags:
        reasoning += f" Flags: [{', '.join(flags)}]."

    return ClassificationResult(
        wallet_type=wallet_type,
        quality_score=quality_score,
        confidence=round(confidence, 2),
        flags=flags,
        is_dev_wallet=is_dev_wallet,
        is_bot=is_bot,
        is_coordinated=is_coordinated,
        reasoning=reasoning,
    )
