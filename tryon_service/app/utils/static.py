"""把 data/ 下的文件路径转成对外静态 URL。"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings


def static_for(path: Path) -> str:
    """绝对路径 → `/static/<相对 data/ 的路径>`。"""
    settings = get_settings()
    try:
        rel = path.resolve().relative_to(settings.data_dir.resolve())
    except ValueError:
        # 不在 data/ 下时，退化为文件名（此类文件不应通过静态服务暴露）
        return f"/static/{path.name}"
    return f"/static/{rel.as_posix()}"
