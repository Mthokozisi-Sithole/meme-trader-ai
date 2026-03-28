from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.behavioral_signal_repo import BehavioralSignalRepository
from app.schemas.behavioral_signal import BehavioralSignalOut
from app.services import behavioral_engine

router = APIRouter(tags=["behavioral"])


@router.get("/signals", response_model=List[BehavioralSignalOut])
async def list_signals(
    token_address: Optional[str] = None,
    chain: Optional[str] = None,
    pattern_type: Optional[str] = None,
    severity: Optional[str] = None,
    active_only: bool = True,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    List behavioral signals with optional filters.

    Query params:
      token_address: Filter by token contract address.
      chain:         Filter by chain.
      pattern_type:  Filter by pattern (accumulation | pre_breakout | fake_breakout | etc.).
      severity:      Filter by severity (info | warning | alert | critical).
      active_only:   Only return currently active signals (default true).
      limit:         Max results (default 50, max 500).
    """
    repo = BehavioralSignalRepository(db)
    signals = await repo.list(
        token_address=token_address,
        chain=chain,
        pattern_type=pattern_type,
        severity=severity,
        active_only=active_only,
        limit=limit,
    )
    return [BehavioralSignalOut.model_validate(s) for s in signals]


@router.get("/signals/{token_address}", response_model=List[BehavioralSignalOut])
async def get_signals_for_token(
    token_address: str,
    db: AsyncSession = Depends(get_db),
):
    """Return all active behavioral signals for a specific token."""
    repo = BehavioralSignalRepository(db)
    signals = await repo.get_active_for_token(token_address=token_address)
    return [BehavioralSignalOut.model_validate(s) for s in signals]


@router.post("/analyze/{token_address}", response_model=List[BehavioralSignalOut])
async def analyze_token(
    token_address: str,
    chain: str = Query(..., description="Chain the token is on (e.g., solana)"),
    token_symbol: Optional[str] = Query(None, description="Optional ticker symbol"),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger on-demand behavioral analysis for a token.

    Fetches the latest timeseries data, runs pattern detection, persists any
    newly detected signals, and returns all active signals for the token.
    """
    return await behavioral_engine.analyze_token(
        db=db,
        token_address=token_address,
        chain=chain,
        token_symbol=token_symbol,
    )


@router.get("/summary")
async def behavioral_summary(
    db: AsyncSession = Depends(get_db),
):
    """
    Return aggregate stats for active behavioral signals.

    Response includes:
      - counts_by_pattern: number of active signals per pattern_type
      - counts_by_severity: number of active signals per severity level
      - total_active: total active signals across all tokens
    """
    repo = BehavioralSignalRepository(db)

    # Fetch all active signals (up to 5000 for stats)
    all_signals = await repo.list(active_only=True, limit=5000)

    counts_by_pattern: dict[str, int] = {}
    counts_by_severity: dict[str, int] = {}

    for signal in all_signals:
        counts_by_pattern[signal.pattern_type] = counts_by_pattern.get(signal.pattern_type, 0) + 1
        counts_by_severity[signal.severity] = counts_by_severity.get(signal.severity, 0) + 1

    return {
        "total_active": len(all_signals),
        "by_pattern": counts_by_pattern,
        "by_severity": counts_by_severity,
    }
