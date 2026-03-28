from datetime import datetime, timedelta
from typing import Optional, Sequence
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert

from app.models.token_timeseries import TokenTimeseries
from app.schemas.token_timeseries import TimeseriesCreate


class TimeseriesRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def upsert(self, data: TimeseriesCreate) -> TokenTimeseries:
        """Insert or update a timeseries bucket (upsert on token_address + chain + timestamp)."""
        values = data.model_dump()
        # Strip timezone info from datetime fields — DB column is TIMESTAMP WITHOUT TIME ZONE
        for key, val in values.items():
            if isinstance(val, datetime) and val.tzinfo is not None:
                values[key] = val.replace(tzinfo=None)

        stmt = (
            insert(TokenTimeseries)
            .values(**values)
            .on_conflict_do_update(
                constraint="uq_timeseries_token_ts",
                set_={
                    k: v
                    for k, v in values.items()
                    if k not in ("token_address", "chain", "timestamp")
                },
            )
            .returning(TokenTimeseries)
        )
        result = await self.db.execute(stmt)
        await self.db.commit()
        return result.scalar_one()

    async def get_history(
        self,
        token_address: str,
        chain: str,
        hours: int = 24,
        limit: int = 500,
    ) -> Sequence[TokenTimeseries]:
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        q = (
            select(TokenTimeseries)
            .where(
                and_(
                    TokenTimeseries.token_address == token_address,
                    TokenTimeseries.chain == chain,
                    TokenTimeseries.timestamp >= cutoff,
                )
            )
            .order_by(TokenTimeseries.timestamp.asc())
            .limit(limit)
        )
        result = await self.db.execute(q)
        return result.scalars().all()

    async def get_latest(
        self, token_address: str, chain: str
    ) -> Optional[TokenTimeseries]:
        q = (
            select(TokenTimeseries)
            .where(
                and_(
                    TokenTimeseries.token_address == token_address,
                    TokenTimeseries.chain == chain,
                )
            )
            .order_by(TokenTimeseries.timestamp.desc())
            .limit(1)
        )
        result = await self.db.execute(q)
        return result.scalar_one_or_none()
