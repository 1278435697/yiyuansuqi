"""数据访问层。"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Garment, TryOnRecord


async def upsert_garment(session: AsyncSession, payload: dict) -> Garment:
    stmt = select(Garment).where(Garment.id == payload["id"])
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing is None:
        existing = Garment(**payload)
        session.add(existing)
    else:
        for key, value in payload.items():
            setattr(existing, key, value)
    await session.commit()
    await session.refresh(existing)
    return existing


async def list_garments(
    session: AsyncSession,
    *,
    category: str | None = None,
    dynasty: str | None = None,
    keyword: str | None = None,
) -> list[Garment]:
    stmt = select(Garment).order_by(Garment.created_at.asc(), Garment.id.asc())
    if category:
        stmt = stmt.where(Garment.category == category)
    if dynasty:
        stmt = stmt.where(Garment.dynasty == dynasty)
    if keyword:
        stmt = stmt.where(Garment.name.like(f"%{keyword}%"))
    return list((await session.execute(stmt)).scalars().all())


async def get_garment(session: AsyncSession, garment_id: str) -> Garment | None:
    return (
        await session.execute(select(Garment).where(Garment.id == garment_id))
    ).scalar_one_or_none()


async def count_garments(session: AsyncSession) -> int:
    return int((await session.execute(select(func.count(Garment.id)))).scalar_one())


async def add_record(session: AsyncSession, payload: dict) -> TryOnRecord:
    record = TryOnRecord(**payload)
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def list_records(
    session: AsyncSession, *, limit: int = 30, offset: int = 0
) -> tuple[list[TryOnRecord], int]:
    total = int((await session.execute(select(func.count(TryOnRecord.id)))).scalar_one())
    stmt = (
        select(TryOnRecord)
        .order_by(TryOnRecord.created_at.desc(), TryOnRecord.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return list((await session.execute(stmt)).scalars().all()), total


async def get_record_by_task(session: AsyncSession, task_id: str) -> TryOnRecord | None:
    stmt = select(TryOnRecord).where(TryOnRecord.task_id == task_id)
    return (await session.execute(stmt)).scalar_one_or_none()
