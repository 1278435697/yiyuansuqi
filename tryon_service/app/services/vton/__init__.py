"""试穿推理后端选择与降级。

resolve("auto") 按 aidge -> hrviton -> tps -> mock 探测；显式指定后端不可用时，
自动降级到下一个可用后端，并把降级原因写入 warnings（绝不静默）。
"""

from __future__ import annotations

from app.config import get_settings
from app.errors import TryOnFailedError
from app.logs import get_logger
from app.services.vton.aidge import AidgeBackend
from app.services.vton.base import TryOnContext, TryOnOutput
from app.services.vton.hrviton import HRVITONBackend
from app.services.vton.mock import MockBackend
from app.services.vton.tps import TPSBackend

logger = get_logger("app.services.vton")

_PRIORITY = ("aidge", "hrviton", "tps", "mock")
_INSTANCES: dict[str, object] = {}


def _instance(name: str):
    if name not in _INSTANCES:
        _INSTANCES[name] = {
            "aidge": AidgeBackend,
            "hrviton": HRVITONBackend,
            "tps": TPSBackend,
            "mock": MockBackend,
        }[name]()
    return _INSTANCES[name]


def resolve(requested: str | None = None) -> tuple[object, str | None]:
    """返回 (backend, fallback_reason)。fallback_reason 为 None 表示按要求命中。"""
    name = (requested or get_settings().vton_backend or "auto").lower()
    candidates = _PRIORITY if name == "auto" else tuple(
        [name] + [n for n in _PRIORITY if n != name]
    )
    first_reason: str | None = None
    for candidate in candidates:
        backend = _instance(candidate)
        ok, reason = backend.available()  # type: ignore[attr-defined]
        if ok:
            if name != "auto" and candidate != name:
                return backend, f"requested={name}_unavailable:{reason};use={candidate}"
            # auto 命中非首选时，把「为什么没用更靠前的那个」原样带出去
            if first_reason is not None:
                return backend, first_reason
            return backend, None
        if first_reason is None:
            first_reason = f"{candidate}_unavailable:{reason}"
    # mock 恒可用，理论不会到这里
    return _instance("mock"), first_reason or "all_backends_unavailable"


def run(ctx: TryOnContext, requested: str | None = None) -> tuple[TryOnOutput, list[str]]:
    """执行试穿；后端内部异常时自动逐级降级。"""
    backend, fallback_reason = resolve(requested)
    warnings: list[str] = []
    if fallback_reason:
        warnings.append(f"vton_fallback:{fallback_reason}")

    # 首选后端之外，按优先级补全降级顺序；若只用 resolve 递推，
    # 「tps 运行期异常 -> resolve("hrviton") 又回到 tps」会形成死路，永远到不了 mock。
    order = [getattr(backend, "name", "")]
    order += [n for n in _PRIORITY if n not in order]

    tried: set[str] = set()
    for name in order:
        if name not in _PRIORITY or name in tried:
            continue
        tried.add(name)
        current = _instance(name)
        if not current.available()[0]:  # type: ignore[attr-defined]
            continue
        try:
            output = current.run(ctx)  # type: ignore[attr-defined]
            logger.info("试穿后端=%s 完成", name)
            return output, warnings
        except Exception as exc:  # noqa: BLE001 - 任何后端异常都需降级
            logger.warning("后端 %s 执行失败: %s", name, exc, exc_info=True)
            warnings.append(f"vton_{name}_error")

    raise TryOnFailedError(detail="所有试穿后端均执行失败")


def status() -> dict[str, object]:
    out: dict[str, object] = {}
    for name in _PRIORITY:
        backend = _instance(name)
        ok, reason = backend.available()  # type: ignore[attr-defined]
        out[name] = {"available": bool(ok), "reason": reason}
    resolved, fallback = resolve("auto")
    out["resolved_auto"] = {"backend": getattr(resolved, "name", "?"), "fallback_reason": fallback}
    return out


__all__ = ["AidgeBackend", "MockBackend", "TPSBackend", "TryOnContext", "TryOnOutput", "resolve", "run", "status"]
