"""把落盘文件路径转成对外静态 URL。

结果图/中间图统一挂在 `settings.results_url_prefix` 下（默认 /tryon-results，
并入平台后可改成 /uploads/tryon 交给平台 nginx），因此这里只认 results_dir。
"""

from __future__ import annotations

from pathlib import Path

from app.config import get_settings


def static_for(path: Path) -> str:
    """结果目录下的绝对路径 → `<results_url_prefix>/<相对 results 根的路径>`。"""
    settings = get_settings()
    prefix = settings.results_url_prefix.rstrip("/")
    try:
        rel = path.resolve().relative_to(settings.results_dir.resolve())
    except ValueError:
        # 不在结果目录里：只回文件名，不做路径穿越（此类文件不该通过静态服务暴露）
        return f"{prefix}/{path.name}"
    return f"{prefix}/{rel.as_posix()}"


_LEGACY_PREFIX = "/static/"


def normalize_legacy_url(url: str | None) -> str | None:
    """把库里残留的旧 `/static/...` 地址改写成当前前缀，返回可直接给前端的字符串。

    静态面拆分前整个 data/ 挂在 /static 下，历史记录把 URL 原样存进了数据库；
    挂载撤掉后这些地址全部 404（命中磁盘缓存时还会被当作新结果返回）。
    - `/static/results/<task>/x.jpg` → `<results_url_prefix>/<task>/x.jpg`
    - `/static/garments|samples/...`  → `<asset_url_prefix>/...`
    - `/static/uploads/...`           → 空串：那是用户真人原图，本就不该再被 URL 直读，
      前端对空 src 有「原图缺失」占位，比留一个必然 404 的活链更诚实。

    注意：改写只解决 URL 拼法，不搬文件。若生产把 results_root 挪到别处，旧图仍需要
    一次性拷贝到新目录，否则改写后照样 404。
    """
    if not url:
        return url
    if not url.startswith(_LEGACY_PREFIX):
        return url
    settings = get_settings()
    rest = url[len(_LEGACY_PREFIX):]
    if rest.startswith("uploads/"):
        return ""
    if rest.startswith("results/"):
        return f"{settings.results_url_prefix.rstrip('/')}/{rest[len('results/'):]}/".rstrip("/")
    return f"{settings.asset_url_prefix.rstrip('/')}/{rest}"
