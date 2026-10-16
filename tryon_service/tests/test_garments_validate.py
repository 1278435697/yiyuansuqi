"""素材元数据校验测试：bbox 面积比 / 关键点数量 / 去重 / 非法项跳过原因。"""

from __future__ import annotations

import copy

import pytest

from app.errors import GarmentNotFoundError
from app.services.garments import (
    AREA_MAX,
    AREA_MIN,
    REQUIRED_KEYPOINTS,
    bbox_area_ratio,
    entry_to_output,
    load_asset,
    static_url,
    to_db_payload,
    valid_entries,
    validate_entry,
)


def _keypoints() -> list[dict[str, float]]:
    """一组合法标注：横向 0.10-0.90、纵向 0.05-0.95，面积比 0.72。"""
    coords = {
        "collar_center": (0.50, 0.05),
        "shoulder_L": (0.18, 0.12),
        "shoulder_R": (0.82, 0.12),
        "sleeve_L_end": (0.10, 0.35),
        "sleeve_R_end": (0.90, 0.35),
        "waist_L": (0.30, 0.48),
        "waist_R": (0.70, 0.48),
        "hem_L": (0.22, 0.95),
        "hem_R": (0.78, 0.95),
    }
    return [{"name": name, "x": x, "y": y} for name, (x, y) in coords.items()]


def _entry(**overrides) -> dict:
    base = {
        "id": "test-robe",
        "name": "测试袍",
        "dynasty": "唐",
        "category": "robe",
        "tags": ["test"],
        "image": "garments/test-robe.png",
        "mask": "garments/test-robe_mask.png",
        "keypoints": _keypoints(),
        "source_text": "《旧唐书·舆服志》",
        "references": ["参考一"],
    }
    base.update(overrides)
    return base


def test_reference_entry_is_valid():
    ok, reason, ratio = validate_entry(_entry())
    assert ok, reason
    assert abs(ratio - bbox_area_ratio(_keypoints())) < 1e-9


@pytest.mark.parametrize(
    "overrides,keyword",
    [
        ({"id": "Bad-ID"}, "id 非法"),
        ({"id": "a"}, "id 非法"),
        ({"id": ""}, "id 非法"),
        ({"name": "  "}, "name 为空"),
        ({"category": "pants"}, "category 非法"),
        ({"keypoints": _keypoints()[:8]}, "关键点数"),
        ({"keypoints": []}, "关键点数"),
    ],
)
def test_invalid_entries_are_rejected(overrides, keyword):
    ok, reason, _ = validate_entry(_entry(**overrides))
    assert not ok and keyword in reason


def test_missing_named_keypoint_detected():
    points = _keypoints()
    points[0] = {"name": "collar_center_x", "x": 0.5, "y": 0.05}  # 数量对但名字缺
    ok, reason, _ = validate_entry(_entry(keypoints=points))
    assert not ok and "缺少关键点" in reason and "collar_center" in reason


def test_out_of_range_coordinate_rejected():
    points = copy.deepcopy(_keypoints())
    points[1]["x"] = 1.4
    ok, reason, _ = validate_entry(_entry(keypoints=points))
    assert not ok and "归一化范围" in reason


def test_bbox_area_ratio_bounds():
    """所有点挤在一起：面积比 < AREA_MIN，视为标注无效（多半是漏标/错标）。"""
    collapsed = [{"name": n, "x": 0.5, "y": 0.5} for n in REQUIRED_KEYPOINTS]
    ok, reason, ratio = validate_entry(_entry(keypoints=collapsed))
    assert not ok and ratio < AREA_MIN and "包围盒面积比" in reason

    tiny = [
        {"name": n, "x": 0.5 + 0.1 * (i % 3), "y": 0.5 + 0.1 * (i // 3)}
        for i, n in enumerate(REQUIRED_KEYPOINTS)
    ]
    assert bbox_area_ratio(tiny) < AREA_MIN

    # 边界值本身必须放行
    edge = [
        {"name": n, "x": 0.0 if i % 2 else 1.0, "y": 0.95 if i % 2 else 0.0}
        for i, n in enumerate(REQUIRED_KEYPOINTS)
    ]
    assert bbox_area_ratio(edge) <= AREA_MAX + 1e-9


def test_valid_entries_dedups_and_keeps_reasons():
    entries = [_entry(), _entry(), _entry(id="bad", category="pants"), "not-a-dict"]
    ok, skipped = valid_entries(entries)
    assert [e["id"] for e in ok] == ["test-robe"]
    assert ok[0]["bbox_area_ratio"] == pytest.approx(0.72, abs=1e-3)
    assert any("id 重复" in s for s in skipped)
    assert any("category 非法" in s for s in skipped)
    assert any("非对象条目" in s for s in skipped)
    assert len(skipped) == 3


def test_payload_and_output_mapping():
    entry = _entry()
    is_valid, _, ratio = validate_entry(entry)
    assert is_valid
    entry["bbox_area_ratio"] = round(ratio, 4)

    payload = to_db_payload(entry)
    assert payload["image_path"] == "garments/test-robe.png"
    assert payload["mask_path"].endswith("_mask.png")
    assert payload["thumb_path"] == payload["image_path"]  # 无缩略图时回退原图
    assert len(payload["keypoints"]) == 9

    out = entry_to_output(entry)
    assert out["image_url"] == static_url("garments/test-robe.png") == "/static/garments/test-robe.png"
    assert out["category"] == "robe"
    assert {kp.name for kp in out["keypoints"]} == set(REQUIRED_KEYPOINTS)


def test_entry_to_output_tolerates_broken_keypoint_items():
    entry = _entry(keypoints=_keypoints() + ["garbage", {"x": 0.1}])
    out = entry_to_output(entry)
    assert len(out["keypoints"]) == 9


def test_load_asset_from_generated_index(sample_garment_ids, settings):
    from app.utils.imageio import normalize_mask

    asset = load_asset(sample_garment_ids[0])
    assert asset.image.ndim == 3 and asset.image.shape[2] == 3
    assert asset.mask.shape == asset.image.shape[:2]
    assert set(asset.keypoints) == set(REQUIRED_KEYPOINTS)
    assert normalize_mask(asset.mask).max() == 255

    with pytest.raises(GarmentNotFoundError):
        load_asset("definitely-not-a-garment")
