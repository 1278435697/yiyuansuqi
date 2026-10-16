"""试穿记录接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_session
from app.logs import get_logger
from app.schemas import HistoryPage, TryOnResult
from app.services import history

logger = get_logger("app.api.history")

router = APIRouter()


@router.get("", response_model=HistoryPage)
@router.get("/", response_model=HistoryPage, include_in_schema=False)
async def list_history(
    session=Depends(get_session),
    limit: int = Query(default=30, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HistoryPage:
    items, total = await history.list_records(session, limit=limit, offset=offset)
    return HistoryPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/{task_id}", response_model=TryOnResult)
async def get_history_detail(task_id: str, session=Depends(get_session)) -> TryOnResult:
    # 不存在时 get_record_result 抛 TaskNotFoundError（404 + 脱敏响应体）
    return await history.get_record_result(session, task_id)


__all__ = ["router"]
