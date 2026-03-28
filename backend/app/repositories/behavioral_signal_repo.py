from datetime import datetime
from typing import Optional, Sequence
from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.behavioral_signal import BehavioralSignal
from app.schemas.behavioral_signal import BehavioralSignalCreate


class BehavioralSignalRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: BehavioralSignalCreate) -> BehavioralSignal:
        """Insert a new behavioral signal record."""
        values = data.model_dump()
        # Strip timezone info from datetime fields — DB column is TIMESTAMP WITHOUT TIME ZONE
        for key, val in values.items():
            if isinstance(val, datetime) and val.tzinfo is not None:
                values[key] = val.replace(tzinfo=None)

        stmt = (
            insert(BehavioralSignal)
            .values(**values)
            .returning(BehavioralSignal)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def list(
        self,
        token_address: Optional[str] = None,
        chain: Optional[str] = None,
        pattern_type: Optional[str] = None,
        severity: Optional[str] = None,
        active_only: bool = True,
        limit: int = 50,
    ) -> Sequence[BehavioralSignal]:
        q = select(BehavioralSignal)

        if token_address is not None:
            q = q.where(BehavioralSignal.token_address == token_address)
        if chain is not None:
            q = q.where(BehavioralSignal.chain == chain)
        if pattern_type is not None:
            q = q.where(BehavioralSignal.pattern_type == pattern_type)
        if severity is not None:
            q = q.where(BehavioralSignal.severity == severity)
        if active_only:
            q = q.where(BehavioralSignal.is_active == True)  # noqa: E712

        q = q.order_by(BehavioralSignal.created_at.desc()).limit(limit)
        result = await self.db.execute(q)
        return result.scalars().all()

    async def deactivate(self, signal_id: int) -> None:
        """Mark a behavioral signal as inactive and record the resolution time."""
        stmt = (
            update(BehavioralSignal)
            .where(BehavioralSignal.id == signal_id)
            .values(is_active=False, resolved_at=datetime.utcnow())
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_active_for_token(self, token_address: str) -> Sequence[BehavioralSignal]:
        q = (
            select(BehavioralSignal)
            .where(
                and_(
                    BehavioralSignal.token_address == token_address,
                    BehavioralSignal.is_active == True,  # noqa: E712
                )
            )
            .order_by(BehavioralSignal.fusion_score.desc(), BehavioralSignal.created_at.desc())
        )
        result = await self.db.execute(q)
        return result.scalars().all()
