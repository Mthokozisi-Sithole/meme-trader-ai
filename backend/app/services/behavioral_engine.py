"""
Behavioral analysis engine — runs pattern detection and persists signals.
"""
from __future__ import annotations

import json
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.behavioral_signal_repo import BehavioralSignalRepository
from app.repositories.timeseries_repo import TimeseriesRepository
from app.schemas.behavioral_signal import BehavioralSignalCreate, BehavioralSignalOut
from app.services.pattern_detector import OHLCVCandle, detect_patterns


async def analyze_token(
    db: AsyncSession,
    token_address: str,
    chain: str,
    token_symbol: Optional[str] = None,
) -> list[BehavioralSignalOut]:
    """
    Orchestrate pattern detection for a token and persist detected signals.

    Steps:
      1. Fetch the last 100 candles from the timeseries repository.
      2. Convert rows to OHLCVCandle objects.
      3. Run detect_patterns() on the candle list.
      4. For each PatternResult with confidence > 30:
         - Deactivate existing active signals of the same pattern_type for this token.
         - Persist a new BehavioralSignal.
      5. Return all currently active signals for this token.

    Args:
        db:            Async SQLAlchemy session.
        token_address: On-chain token address.
        chain:         Chain identifier (e.g., "solana", "ethereum").
        token_symbol:  Optional ticker symbol for display.

    Returns:
        List of active BehavioralSignalOut for this token after the analysis run.
    """
    ts_repo = TimeseriesRepository(db)
    signal_repo = BehavioralSignalRepository(db)

    # 1. Fetch last 100 candles (up to 48h window, limit 100)
    rows = await ts_repo.get_history(
        token_address=token_address,
        chain=chain,
        hours=48,
        limit=100,
    )

    if not rows:
        # No timeseries data — return existing active signals unchanged
        active = await signal_repo.get_active_for_token(token_address)
        return [BehavioralSignalOut.model_validate(s) for s in active]

    # 2. Convert ORM rows to OHLCVCandle dataclasses
    candles: list[OHLCVCandle] = [
        OHLCVCandle(
            timestamp=row.timestamp.timestamp() if hasattr(row.timestamp, "timestamp") else float(row.timestamp),
            open=row.price_open or 0.0,
            high=row.price_high or 0.0,
            low=row.price_low or 0.0,
            close=row.price_close or 0.0,
            volume_usd=row.volume_usd or 0.0,
            buy_pressure_pct=row.buy_pressure_pct,
        )
        for row in rows
    ]

    # 3. Detect patterns
    patterns = detect_patterns(candles, window=20)

    # 4. Persist signals with confidence > 30
    for pattern in patterns:
        if pattern.confidence <= 30.0:
            continue

        # Deactivate existing active signals of the same pattern_type for this token
        existing = await signal_repo.list(
            token_address=token_address,
            chain=chain,
            pattern_type=pattern.pattern_type,
            active_only=True,
        )
        for old_signal in existing:
            await signal_repo.deactivate(old_signal.id)

        # Build the create payload
        signal_data = BehavioralSignalCreate(
            token_address=token_address,
            token_symbol=token_symbol,
            chain=chain,
            pattern_type=pattern.pattern_type,
            signal_label=pattern.signal_label,
            confidence=round(pattern.confidence, 2),
            severity=pattern.severity,
            supporting_metrics=json.dumps(pattern.supporting_metrics) if pattern.supporting_metrics else None,
            contributing_factors=json.dumps(pattern.contributing_factors) if pattern.contributing_factors else None,
            raw_data_snapshot=None,
            is_active=True,
            fusion_score=round(pattern.confidence, 2),  # seed fusion_score from confidence
        )
        await signal_repo.create(signal_data)

    # 5. Return all active signals for this token
    active_signals = await signal_repo.get_active_for_token(token_address)
    return [BehavioralSignalOut.model_validate(s) for s in active_signals]
