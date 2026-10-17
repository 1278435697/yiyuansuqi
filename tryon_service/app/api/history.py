"""试穿记录接口。"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from fastapi.responses import FileResponse, Response

from app.api.deps import get_session
from app.config import get_settings
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


@router.delete("/{task_id}", status_code=204)
async def delete_history_record(task_id: str, session=Depends(get_session)) -> Response:
    """删除试穿记录（数据库行 + 结果目录 + 原图目录）。幂等：不存在也返回 204。"""
    await history.delete_record(session, task_id)
    return Response(status_code=204)


@router.get("/{task_id}/person-source", include_in_schema=False)
async def get_person_source(task_id: str, session=Depends(get_session)) -> FileResponse:
    """提供用户原图，仅当数据库记录存在时才可访问。"""
    history.validate_task_id(task_id)
    record = await history.repos.get_record_by_task(session, task_id)
    if record is None:
        from app.errors import TaskNotFoundError

        raise TaskNotFoundError()
    settings = get_settings()
    person_file = settings.person_sources_dir / task_id / "person_source.jpg"
    if not person_file.is_file():
        from app.errors import TaskNotFoundError

        raise TaskNotFoundError()
    return FileResponse(person_file, media_type="image/jpeg")


__all__ = ["router"]
