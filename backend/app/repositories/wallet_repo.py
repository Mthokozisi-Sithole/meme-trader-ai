from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.wallet import Wallet
from app.models.wallet_transaction import WalletTransaction
from app.schemas.wallet import WalletCreate, WalletTransactionCreate


class WalletRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, data: WalletCreate) -> Wallet:
        """Insert or update a wallet record (upsert on address + chain)."""
        values = data.model_dump()
        # Strip timezone info from datetime fields — DB column is TIMESTAMP WITHOUT TIME ZONE
        for key, val in values.items():
            if isinstance(val, datetime) and val.tzinfo is not None:
                values[key] = val.replace(tzinfo=None)

        # Provide defaults for timestamp fields if not supplied
        now = datetime.utcnow()
        values.setdefault("first_seen", now)
        values.setdefault("last_active", now)

        stmt = (
            insert(Wallet)
            .values(**values)
            .on_conflict_do_update(
                index_elements=["address"],
                set_={k: v for k, v in values.items() if k not in ("address", "chain")},
            )
            .returning(Wallet)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def get(self, address: str, chain: str) -> Optional[Wallet]:
        result = await self.db.execute(
            select(Wallet).where(
                and_(Wallet.address == address, Wallet.chain == chain)
            )
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        wallet_type: Optional[str] = None,
        flagged: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[Wallet]:
        q = select(Wallet)

        if wallet_type is not None:
            q = q.where(Wallet.wallet_type == wallet_type)
        if flagged is not None:
            q = q.where(Wallet.flagged == flagged)

        q = q.order_by(Wallet.quality_score.desc()).offset(offset).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def add_transaction(self, data: WalletTransactionCreate) -> WalletTransaction:
        values = data.model_dump()
        # Strip timezone info from datetime fields
        for key, val in values.items():
            if isinstance(val, datetime) and val.tzinfo is not None:
                values[key] = val.replace(tzinfo=None)

        stmt = (
            insert(WalletTransaction)
            .values(**values)
            .returning(WalletTransaction)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def get_transactions(
        self, wallet_address: str, limit: int = 50
    ) -> Sequence[WalletTransaction]:
        q = (
            select(WalletTransaction)
            .where(WalletTransaction.wallet_address == wallet_address)
            .order_by(WalletTransaction.timestamp.desc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_transactions_for_token(
        self, token_address: str, limit: int = 100
    ) -> Sequence[WalletTransaction]:
        q = (
            select(WalletTransaction)
            .where(WalletTransaction.token_address == token_address)
            .order_by(WalletTransaction.timestamp.desc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        return result.scalars().all()
