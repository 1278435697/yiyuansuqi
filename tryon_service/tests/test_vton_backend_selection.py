"""试穿后端选择与降级测试：auto 优先级 + 显式指定后的 fallback 原因。"""

from __future__ import annotations

import numpy as np
import pytest

from app.errors import TryOnFailedError
from app.services import vton
from app.services.vton import hrviton as hrviton_mod
from app.services.vton import mock as mock_mod
from app.services.vton import tps as tps_mod
from app.services.vton.base import TryOnOutput


def _hrviton_state(monkeypatch, ok: bool, reason: str | None) -> None:
    monkeypatch.setattr(
        hrviton_mod.HRVITONBackend, "available", lambda self: (ok, None if ok else reason)
    )


@pytest.fixture
def no_hrviton(monkeypatch):
    """模拟本机最常见的情况：无 torch / 无 CUDA / 无权重。"""
    _hrviton_state(monkeypatch, False, "torch_cuda_unavailable")


def test_mock_is_always_available():
    backend, reason = vton.resolve("mock")
    assert backend.name == "mock"
    assert reason is None


def test_auto_skips_hrviton_when_weights_or_cuda_missing(no_hrviton):
    backend, reason = vton.resolve("auto")
    assert backend.name in {"tps", "mock"}
    assert reason is not None and reason.startswith("hrviton_unavailable:")
    assert "torch_cuda_unavailable" in reason


def test_auto_returns_no_reason_when_hrviton_ready(monkeypatch):
    _hrviton_state(monkeypatch, True, None)
    backend, reason = vton.resolve("auto")
    assert backend.name == "hrviton"
    assert reason is None


def test_explicit_request_falls_back_with_visible_reason(no_hrviton):
    """显式点名 hrviton 但不可用：必须降级，同时把原因写进返回值（绝不静默）。"""
    backend, reason = vton.resolve("hrviton")
    assert backend.name in {"tps", "mock"}
    assert "requested=hrviton_unavailable" in reason
    assert f"use={backend.name}" in reason


def test_status_reports_every_backend(no_hrviton):
    info = vton.status()
    assert set(info) >= {"hrviton", "tps", "mock", "resolved_auto"}
    assert info["mock"]["available"] is True
    assert info["hrviton"]["available"] is False
    assert info["resolved_auto"]["backend"] in {"tps", "mock"}


def test_run_degrades_to_mock_when_tps_raises(no_hrviton, monkeypatch):
    """tps 可用性自检通过但运行期抛异常时，必须继续降到 mock，而不是直接失败。"""

    def _boom(self, ctx):
        raise RuntimeError("singular tps system")

    sentinel = TryOnOutput(
        result=np.zeros((8, 8, 3), dtype=np.uint8), backend="mock", notes=["mock_backend_used"]
    )
    monkeypatch.setattr(tps_mod.TPSBackend, "available", lambda self: (True, None))
    monkeypatch.setattr(tps_mod.TPSBackend, "run", _boom)
    monkeypatch.setattr(mock_mod.MockBackend, "run", lambda self, ctx: sentinel)

    output, warnings = vton.run(None, requested="auto")  # ctx 未被 mock 桩使用
    assert output.backend == "mock"
    assert "vton_tps_error" in warnings
    assert any(w.startswith("vton_fallback:") for w in warnings)


def test_run_raises_when_every_backend_fails(no_hrviton, monkeypatch):
    monkeypatch.setattr(tps_mod.TPSBackend, "run", lambda self, ctx: (_ for _ in ()).throw(ValueError("x")))
    monkeypatch.setattr(mock_mod.MockBackend, "run", lambda self, ctx: (_ for _ in ()).throw(ValueError("y")))

    with pytest.raises(TryOnFailedError):
        vton.run(None, requested="auto")
