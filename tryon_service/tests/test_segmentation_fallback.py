"""分割 Provider 链降级测试：上层全部不可用时仍要给出可用掩码。"""

from __future__ import annotations

import numpy as np
import pytest

from app.services import segmentation
from app.services.segmentation import heuristic as heuristic_mod
from app.services.segmentation import mediapipe_selfie, u2net, vitongpu


def _unavailable(self) -> tuple[bool, str | None]:
    return False, "forced_unavailable_by_test"


@pytest.fixture
def person_image():
    from app.config import get_settings
    from app.utils.imageio import load_rgb
    from scripts.gen_sample_garments import render_sample_person

    settings = get_settings()
    rel = render_sample_person(settings.data_dir)
    return load_rgb((settings.data_dir / rel).read_bytes(), label="人像图")


def test_chain_reports_all_providers():
    status = segmentation.status()
    assert set(status) >= {"vitongpu", "u2net", "mediapipe_selfie", "heuristic"}
    # heuristic 是零依赖兜底，必须永远可用
    assert status["heuristic"]["available"] is True


def test_all_model_providers_down(monkeypatch, person_image):
    """三层模型 Provider 全不可用 + 启发式推理异常 → 退到中心前景先验，仍出掩码。"""
    monkeypatch.setattr(vitongpu.VitonGPUProvider, "available", _unavailable)
    monkeypatch.setattr(u2net.U2NetProvider, "available", _unavailable)
    monkeypatch.setattr(mediapipe_selfie.MediaPipeSelfieProvider, "available", _unavailable)
    monkeypatch.setattr(
        heuristic_mod.HeuristicProvider,
        "segment",
        lambda self, rgb: (_ for _ in ()).throw(RuntimeError("no opencv")),
    )

    result, warnings = segmentation.get_person_mask(person_image)

    assert result.person.shape == person_image.shape[:2]
    assert result.person.dtype == np.uint8
    coverage = float((result.person > 127).mean())
    assert 0.01 < coverage < 0.99, f"兜底掩码覆盖率异常: {coverage}"
    assert result.provider == "prior_box"
    for name in ("vitongpu", "u2net", "mediapipe_selfie"):
        assert f"segmentation_{name}_unavailable" in warnings
    assert "segmentation_heuristic_error" in warnings
    assert "segmentation_all_failed_use_prior" in warnings


def test_three_layer_chain_still_returns_mask(monkeypatch, person_image):
    """只砍掉最优三层：启发式（GrabCut / 显著性）必须给出可用前景。"""
    monkeypatch.setattr(vitongpu.VitonGPUProvider, "available", _unavailable)
    monkeypatch.setattr(u2net.U2NetProvider, "available", _unavailable)
    monkeypatch.setattr(mediapipe_selfie.MediaPipeSelfieProvider, "available", _unavailable)

    result, warnings = segmentation.get_person_mask(person_image)
    assert result.provider in {"heuristic", "grabcut", "salience", "prior_box"}
    assert float((result.person > 127).mean()) > 0.01
    assert any(w.startswith("segmentation_fallback_to_") or "unavailable" in w for w in warnings)


def test_low_quality_mask_is_rejected(person_image):
    """全白图 → 掩码覆盖率 100%，质量底线必须拦下并继续降级。"""
    blank = np.full(person_image.shape, 255, dtype=np.uint8)
    ok, detail = segmentation._sanity_check(blank)
    assert not ok and "covers_whole_image" in detail

    empty = np.zeros(person_image.shape[:2], dtype=np.uint8)
    ok, detail = segmentation._sanity_check(empty)
    assert not ok and "too_small" in detail

    normal = (person_image.mean(axis=2) > 200).astype(np.uint8) * 255
    if 0.01 < float((normal > 127).mean()) < 0.99:
        assert segmentation._sanity_check(normal)[0]
