"""
Time-series behavioral pattern detection.

Patterns:
  accumulation       — steady buys, price flat/rising, volume building
  pre_breakout       — price compression + volume spike
  fake_breakout      — price spike followed by immediate dump
  liquidity_trap     — thin liquidity + sudden price movement
  momentum_ignition  — rapid coordinated price push
  volume_anomaly     — volume 3x+ normal with minimal price movement (wash trading signal)
  wash_trading       — repetitive buy/sell same wallets
  breakdown          — price dropping below support + increasing sells
  consolidation      — low volatility range-bound
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class OHLCVCandle:
    timestamp: float    # unix
    open: float
    high: float
    low: float
    close: float
    volume_usd: float
    buy_pressure_pct: Optional[float] = None  # 0-100


@dataclass
class PatternResult:
    pattern_type: str
    confidence: float           # 0-100
    severity: str               # info | warning | alert | critical
    signal_label: str
    supporting_metrics: dict = field(default_factory=dict)
    contributing_factors: dict = field(default_factory=dict)


def _avg(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _safe_stdev(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return statistics.stdev(values)


def detect_patterns(candles: list[OHLCVCandle], window: int = 20) -> list[PatternResult]:
    """
    Detect behavioral patterns from OHLCV candle data.

    Args:
        candles: List of OHLCV candles ordered oldest → newest.
        window:  Rolling window for baseline calculations (default 20).

    Returns:
        List of PatternResult objects for each detected pattern.
    """
    results: list[PatternResult] = []

    if len(candles) < 3:
        return results

    # Use the last `window` candles as baseline for averages
    baseline = candles[-window:] if len(candles) >= window else candles
    avg_volume = _avg([c.volume_usd for c in baseline])

    # Recent candles for pattern checks
    recent = candles[-5:] if len(candles) >= 5 else candles
    last = candles[-1]
    prev = candles[-2] if len(candles) >= 2 else None

    # ---- ACCUMULATION ----
    # last 5 closes trending up >5%, volume increasing, buy_pressure >55%
    if len(recent) >= 5:
        close_prices = [c.close for c in recent]
        if close_prices[0] > 0:
            price_change_pct = (close_prices[-1] - close_prices[0]) / close_prices[0] * 100
        else:
            price_change_pct = 0.0
        volumes_increasing = all(
            recent[i].volume_usd >= recent[i - 1].volume_usd
            for i in range(1, len(recent))
        )
        bp_values = [c.buy_pressure_pct for c in recent if c.buy_pressure_pct is not None]
        avg_bp = _avg(bp_values) if bp_values else None

        if price_change_pct > 5.0 and volumes_increasing and (avg_bp is None or avg_bp > 55.0):
            confidence = min(100.0, 50.0 + price_change_pct * 2.0)
            results.append(PatternResult(
                pattern_type="accumulation",
                confidence=round(confidence, 2),
                severity="info",
                signal_label="Accumulation Phase Detected",
                supporting_metrics={
                    "price_change_5c_pct": round(price_change_pct, 2),
                    "avg_buy_pressure_pct": round(avg_bp, 2) if avg_bp is not None else None,
                    "volumes_increasing": volumes_increasing,
                },
                contributing_factors={
                    "price_trend": 0.5,
                    "volume_build": 0.3,
                    "buy_pressure": 0.2,
                },
            ))

    # ---- PRE_BREAKOUT ----
    # price range narrowing + volume spiking >2x avg
    if len(candles) >= 10 and prev is not None:
        recent_ranges = [(c.high - c.low) for c in candles[-10:]]
        early_ranges = recent_ranges[:5]
        late_ranges = recent_ranges[5:]
        avg_early_range = _avg(early_ranges)
        avg_late_range = _avg(late_ranges)
        range_narrowing = avg_early_range > 0 and avg_late_range < avg_early_range * 0.75

        current_volume_spike = avg_volume > 0 and last.volume_usd > avg_volume * 2.0

        if range_narrowing and current_volume_spike:
            confidence = 70.0
            results.append(PatternResult(
                pattern_type="pre_breakout",
                confidence=round(confidence, 2),
                severity="alert",
                signal_label="Pre-Breakout Compression",
                supporting_metrics={
                    "avg_early_range": round(avg_early_range, 8),
                    "avg_late_range": round(avg_late_range, 8),
                    "volume_multiplier": round(last.volume_usd / avg_volume, 2) if avg_volume > 0 else None,
                },
                contributing_factors={
                    "range_compression": 0.6,
                    "volume_spike": 0.4,
                },
            ))

    # ---- FAKE_BREAKOUT ----
    # candle with high >20% above prev close, bearish close (close < open), high sell pressure
    if prev is not None and prev.close > 0:
        spike_pct = (last.high - prev.close) / prev.close * 100
        bearish_close = last.close < last.open
        bp = last.buy_pressure_pct
        high_sell_pressure = bp is not None and bp < 40.0

        if spike_pct > 20.0 and bearish_close:
            confidence = 60.0 + (spike_pct - 20.0) * 0.5
            if high_sell_pressure:
                confidence += 15.0
            results.append(PatternResult(
                pattern_type="fake_breakout",
                confidence=round(min(confidence, 100.0), 2),
                severity="alert",
                signal_label="Fake Breakout — Bearish Reversal",
                supporting_metrics={
                    "spike_pct_above_prev_close": round(spike_pct, 2),
                    "bearish_close": bearish_close,
                    "buy_pressure_pct": bp,
                },
                contributing_factors={
                    "spike_magnitude": 0.5,
                    "bearish_close": 0.3,
                    "sell_pressure": 0.2,
                },
            ))

    # ---- LIQUIDITY_TRAP ----
    # single candle +15% spike, followed by -10% next candle, low volume environment
    if len(candles) >= 3:
        c_prev2 = candles[-3]
        c_prev1 = candles[-2]
        c_last = candles[-1]
        if c_prev2.close > 0 and c_prev1.open > 0:
            spike_up_pct = (c_prev1.high - c_prev2.close) / c_prev2.close * 100
            dump_pct = (c_prev1.close - c_last.close) / c_prev1.close * 100 if c_prev1.close > 0 else 0
            low_vol_env = avg_volume > 0 and _avg([c.volume_usd for c in candles[-5:]]) < avg_volume * 0.6

            if spike_up_pct > 15.0 and dump_pct > 10.0 and low_vol_env:
                confidence = 65.0 + min(spike_up_pct - 15.0, 20.0)
                results.append(PatternResult(
                    pattern_type="liquidity_trap",
                    confidence=round(confidence, 2),
                    severity="critical",
                    signal_label="Liquidity Trap — Pump and Dump Risk",
                    supporting_metrics={
                        "spike_pct": round(spike_up_pct, 2),
                        "dump_pct": round(dump_pct, 2),
                        "low_volume_environment": low_vol_env,
                    },
                    contributing_factors={
                        "price_spike": 0.4,
                        "immediate_dump": 0.4,
                        "thin_liquidity": 0.2,
                    },
                ))

    # ---- MOMENTUM_IGNITION ----
    # 3+ consecutive green candles each +5%, volume multiplier >3x avg
    if len(candles) >= 4:
        last3 = candles[-3:]
        consecutive_green = all(c.close > c.open for c in last3)
        each_5pct = all(
            c.open > 0 and (c.close - c.open) / c.open * 100 >= 5.0
            for c in last3
        )
        vol_mult = (
            _avg([c.volume_usd for c in last3]) / avg_volume
            if avg_volume > 0 else 0.0
        )

        if consecutive_green and each_5pct and vol_mult > 3.0:
            confidence = min(100.0, 65.0 + vol_mult * 3.0)
            results.append(PatternResult(
                pattern_type="momentum_ignition",
                confidence=round(confidence, 2),
                severity="alert",
                signal_label="Momentum Ignition — Coordinated Price Push",
                supporting_metrics={
                    "consecutive_green_candles": 3,
                    "volume_multiplier": round(vol_mult, 2),
                    "min_gain_pct": 5.0,
                },
                contributing_factors={
                    "consecutive_greens": 0.4,
                    "each_5pct_gain": 0.3,
                    "volume_surge": 0.3,
                },
            ))

    # ---- VOLUME_ANOMALY ----
    # volume >3x 20-period avg but price change <2% (wash trading indicator)
    if prev is not None and avg_volume > 0 and prev.close > 0:
        vol_ratio = last.volume_usd / avg_volume
        price_change_abs = abs((last.close - prev.close) / prev.close * 100)

        if vol_ratio > 3.0 and price_change_abs < 2.0:
            confidence = min(100.0, 50.0 + (vol_ratio - 3.0) * 10.0)
            results.append(PatternResult(
                pattern_type="volume_anomaly",
                confidence=round(confidence, 2),
                severity="warning",
                signal_label="Volume Anomaly — Possible Wash Trading",
                supporting_metrics={
                    "volume_multiplier": round(vol_ratio, 2),
                    "price_change_pct": round(price_change_abs, 3),
                    "avg_volume_usd": round(avg_volume, 2),
                },
                contributing_factors={
                    "volume_spike": 0.6,
                    "minimal_price_movement": 0.4,
                },
            ))

    # ---- WASH_TRADING ----
    # alternating buy/sell pressure waves with minimal net price movement
    if len(candles) >= 6:
        last6 = candles[-6:]
        bp_values = [c.buy_pressure_pct for c in last6 if c.buy_pressure_pct is not None]
        if len(bp_values) >= 4:
            # Look for alternating high/low buy pressure
            alternations = sum(
                1 for i in range(1, len(bp_values))
                if abs(bp_values[i] - bp_values[i - 1]) > 20.0
            )
            # Net price change over 6 candles
            net_change = abs(
                (last6[-1].close - last6[0].close) / last6[0].close * 100
            ) if last6[0].close > 0 else 100.0

            if alternations >= 3 and net_change < 3.0:
                confidence = 55.0 + alternations * 5.0
                results.append(PatternResult(
                    pattern_type="wash_trading",
                    confidence=round(min(confidence, 100.0), 2),
                    severity="warning",
                    signal_label="Wash Trading Pattern Detected",
                    supporting_metrics={
                        "bp_alternations": alternations,
                        "net_price_change_pct": round(net_change, 3),
                        "bp_values": [round(v, 1) for v in bp_values],
                    },
                    contributing_factors={
                        "bp_alternations": 0.7,
                        "flat_price": 0.3,
                    },
                ))

    # ---- BREAKDOWN ----
    # 3+ consecutive red candles, each close lower, volume increasing on down moves
    if len(candles) >= 4:
        last3 = candles[-3:]
        consecutive_red = all(c.close < c.open for c in last3)
        each_lower_close = all(
            last3[i].close < last3[i - 1].close
            for i in range(1, len(last3))
        )
        volume_increasing = all(
            last3[i].volume_usd >= last3[i - 1].volume_usd
            for i in range(1, len(last3))
        )

        if consecutive_red and each_lower_close:
            confidence = 60.0
            if volume_increasing:
                confidence += 20.0
            results.append(PatternResult(
                pattern_type="breakdown",
                confidence=round(confidence, 2),
                severity="alert",
                signal_label="Breakdown — Accelerating Sell Pressure",
                supporting_metrics={
                    "consecutive_red_candles": 3,
                    "each_close_lower": each_lower_close,
                    "volume_increasing_on_down": volume_increasing,
                },
                contributing_factors={
                    "consecutive_reds": 0.5,
                    "lower_lows": 0.3,
                    "increasing_volume": 0.2,
                },
            ))

    # ---- CONSOLIDATION ----
    # ATR <2% over last 10 candles, volume declining
    if len(candles) >= 10:
        last10 = candles[-10:]
        # ATR approximation: average of (high - low) / close
        atr_pcts = [
            (c.high - c.low) / c.close * 100
            for c in last10
            if c.close > 0
        ]
        avg_atr = _avg(atr_pcts) if atr_pcts else 100.0

        vols_last10 = [c.volume_usd for c in last10]
        vol_declining = (
            _avg(vols_last10[5:]) < _avg(vols_last10[:5]) * 0.8
            if len(vols_last10) >= 10 else False
        )

        if avg_atr < 2.0:
            confidence = 50.0 + (2.0 - avg_atr) * 20.0
            if vol_declining:
                confidence += 10.0
            results.append(PatternResult(
                pattern_type="consolidation",
                confidence=round(min(confidence, 100.0), 2),
                severity="info",
                signal_label="Consolidation — Range-Bound Price Action",
                supporting_metrics={
                    "avg_atr_pct": round(avg_atr, 3),
                    "volume_declining": vol_declining,
                    "candles_analyzed": len(last10),
                },
                contributing_factors={
                    "low_atr": 0.7,
                    "declining_volume": 0.3,
                },
            ))

    return results
