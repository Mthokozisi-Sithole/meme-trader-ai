from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.wallet_repo import WalletRepository
from app.schemas.wallet import WalletOut, WalletTransactionOut
from app.services.wallet_classifier import WalletMetrics, classify_wallet

router = APIRouter(tags=["wallets"])


@router.get("", response_model=List[WalletOut])
async def list_wallets(
    chain: Optional[str] = None,
    wallet_type: Optional[str] = None,
    flagged: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """
    List tracked wallets with optional filters.

    Query params:
      chain:       Filter by chain (e.g., "solana", "ethereum").
      wallet_type: Filter by classification (smart_money | dev | bot | whale | sniper | dumper | retail | unknown).
      flagged:     If true, return only flagged wallets.
      limit:       Max results (default 50, max 500).
      offset:      Pagination offset.
    """
    repo = WalletRepository(db)
    wallets = await repo.list(
        wallet_type=wallet_type,
        flagged=flagged,
        limit=limit,
        offset=offset,
    )
    # Apply chain filter post-query (repo.list doesn't filter by chain currently)
    if chain is not None:
        wallets = [w for w in wallets if w.chain == chain]
    return [WalletOut.model_validate(w) for w in wallets]


@router.get("/{address}", response_model=WalletOut)
async def get_wallet(
    address: str,
    chain: str = Query(..., description="Chain the wallet is on (e.g., solana)"),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a single wallet by address and chain."""
    repo = WalletRepository(db)
    wallet = await repo.get(address=address, chain=chain)
    if wallet is None:
        raise HTTPException(status_code=404, detail=f"Wallet {address} not found on {chain}")
    return WalletOut.model_validate(wallet)


@router.get("/{address}/transactions", response_model=List[WalletTransactionOut])
async def get_wallet_transactions(
    address: str,
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """Return transaction history for a wallet address."""
    repo = WalletRepository(db)
    txns = await repo.get_transactions(wallet_address=address, limit=limit)
    return [WalletTransactionOut.model_validate(t) for t in txns]


@router.post("/{address}/classify")
async def classify_wallet_endpoint(
    address: str,
    chain: str = Query(..., description="Chain the wallet is on"),
    db: AsyncSession = Depends(get_db),
):
    """
    Re-classify a wallet by running the wallet classifier on its stored metrics.

    Returns the classification result without persisting — call the upsert endpoint
    separately to save updated classification data.
    """
    repo = WalletRepository(db)
    wallet = await repo.get(address=address, chain=chain)
    if wallet is None:
        raise HTTPException(status_code=404, detail=f"Wallet {address} not found on {chain}")

    metrics = WalletMetrics(
        address=wallet.address,
        chain=wallet.chain,
        total_txns=wallet.total_txns,
        win_rate=wallet.win_rate,
        avg_hold_hours=wallet.avg_hold_hours,
        total_realized_pnl_usd=wallet.total_realized_pnl_usd,
        rug_exits=wallet.rug_exits,
        times_early_buyer=wallet.times_early_buyer,
        is_first_buyer_pattern=wallet.is_dev_wallet or wallet.times_early_buyer > 3,
        hold_duration_variance=0.5,  # default: moderate variance if not stored
        avg_buy_slippage=None,
        coordinated_addresses=[],
    )

    result = classify_wallet(metrics)

    return {
        "address": address,
        "chain": chain,
        "current_type": wallet.wallet_type,
        "classification": {
            "wallet_type": result.wallet_type,
            "quality_score": result.quality_score,
            "confidence": result.confidence,
            "flags": result.flags,
            "is_dev_wallet": result.is_dev_wallet,
            "is_bot": result.is_bot,
            "is_coordinated": result.is_coordinated,
            "reasoning": result.reasoning,
        },
    }
