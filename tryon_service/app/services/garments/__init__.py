"""服饰素材库：磁盘 index.json + SQLite 双向装载、关键点校验。"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings
from app.errors import GarmentNotFoundError
from app.logs import get_logger
from app.schemas import GarmentCategory, Keypoint, TraceCard

logger = get_logger("app.services.garments")

# 每件古装必须标注的 9 个关键点
REQUIRED_KEYPOINTS: tuple[str, ...] = (
    "collar_center",
    "shoulder_L",
    "shoulder_R",
    "sleeve_L_end",
    "sleeve_R_end",
    "waist_L",
    "waist_R",
    "hem_L",
    "hem_R",
)
VALID_CATEGORIES = {"top", "dress", "skirt", "robe"}
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,63}$")
AREA_MIN, AREA_MAX = 0.05, 0.95


@dataclass
class GarmentAsset:
    """试穿管线使用的素材对象（图 + 掩码 + 关键点已加载到内存）。"""

    id: str
    name: str
    dynasty: str
    category: str
    tags: list[str]
    image: np.ndarray  # RGB (H,W,3)
    mask: np.ndarray  # (H,W) uint8 0/255
    keypoints: dict[str, tuple[float, float]] = field(default_factory=dict)
    source_text: str = ""
    references: list[str] = field(default_factory=list)

    @property
    def kp_list(self) -> list[Keypoint]:
        return [
            Keypoint(name=name, x=float(x), y=float(y)) for name, (x, y) in self.keypoints.items()
        ]


def _asset_root() -> Path:
    return get_settings().garments_dir


def static_url(rel_path: str) -> str:
    """data/ 下的相对路径（如 garments/xxx.png）→ 对外可访问 URL。

    前缀取 settings.asset_url_prefix：旧版直接挂在 /static 下并整目录暴露 data/，
    并入平台后改成只挂素材/示例图两类，顺带清掉历史数据里残留的 static/ 前缀。
    """
    clean = rel_path.replace("\\", "/").lstrip("/")
    if clean.startswith("static/"):
        clean = clean[len("static/"):]
    return f"{get_settings().asset_url_prefix.rstrip('/')}/{clean}"


def validate_entry(entry: dict[str, Any]) -> tuple[bool, str, float]:
    """校验单条素材元数据。返回 (是否合法, 原因, bbox 面积比)。"""
    gid = str(entry.get("id", "")).strip()
    if not gid or not _ID_RE.match(gid):
        return False, "id 非法（需小写字母/数字/-/_，长度 2-64）", 0.0
    if not str(entry.get("name", "")).strip():
        return False, "name 为空", 0.0
    if entry.get("category") not in VALID_CATEGORIES:
        return False, f"category 非法：{entry.get('category')}", 0.0

    points = entry.get("keypoints") or []
    names = [str(p.get("name", "")) for p in points if isinstance(p, dict)]
    if len(names) != len(REQUIRED_KEYPOINTS):
        return False, f"关键点数应为 {len(REQUIRED_KEYPOINTS)}，实际 {len(names)}", 0.0
    missing = set(REQUIRED_KEYPOINTS) - set(names)
    if missing:
        return False, f"缺少关键点：{sorted(missing)}", 0.0
    for p in points:
        x, y = float(p.get("x", -1)), float(p.get("y", -1))
        if not (0.0 <= x <= 1.0 and 0.0 <= y <= 1.0):
            return False, f"关键点 {p.get('name')} 坐标超出归一化范围", 0.0

    ratio = bbox_area_ratio(points)
    if not AREA_MIN <= ratio <= AREA_MAX:
        return False, f"关键点包围盒面积比 {ratio:.3f} 超出 [{AREA_MIN}, {AREA_MAX}]", ratio
    return True, "", ratio


def bbox_area_ratio(points: list[dict[str, Any]]) -> float:
    xs = [float(p["x"]) for p in points]
    ys = [float(p["y"]) for p in points]
    return max(0.0, (max(xs) - min(xs)) * (max(ys) - min(ys)))


def load_index() -> list[dict[str, Any]]:
    index_path = _asset_root() / "index.json"
    if not index_path.is_file():
        logger.warning("素材索引不存在：%s，可运行 scripts/gen_sample_garments.py 生成", index_path)
        return []
    try:
        data = json.loads(index_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("素材索引 JSON 解析失败: %s", exc)
        return []
    entries = data.get("garments") if isinstance(data, dict) else data
    if not isinstance(entries, list):
        logger.error("素材索引格式错误，期望列表或 {garments: [...]})")
        return []
    return entries


def valid_entries(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[str]]:
    """去重 + 校验，返回 (可用素材, 跳过原因)。"""
    seen: set[str] = set()
    ok: list[dict[str, Any]] = []
    skipped: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            skipped.append("非对象条目已忽略")
            continue
        is_valid, reason, ratio = validate_entry(entry)
        gid = str(entry.get("id", "?"))
        if not is_valid:
            skipped.append(f"{gid}: {reason}")
            continue
        if gid in seen:
            skipped.append(f"{gid}: id 重复")
            continue
        seen.add(gid)
        entry["bbox_area_ratio"] = round(ratio, 4)
        ok.append(entry)
    if skipped:
        logger.warning("素材校验跳过 %d 条: %s", len(skipped), "; ".join(skipped))
    return ok, skipped


def to_db_payload(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": entry["id"],
        "name": entry["name"],
        "dynasty": entry.get("dynasty", "未知"),
        "category": entry["category"],
        "tags": list(entry.get("tags") or []),
        "image_path": entry["image"],
        "mask_path": entry.get("mask"),
        "thumb_path": entry.get("thumb") or entry["image"],
        "keypoints": list(entry.get("keypoints") or []),
        "bbox_area_ratio": float(entry.get("bbox_area_ratio", 0.0)),
        "source_text": entry.get("source_text", ""),
        "references": list(entry.get("references") or []),
    }


def entry_to_output(entry: dict[str, Any]) -> dict[str, Any]:
    thumb = entry.get("thumb") or entry["image"]
    keypoints = [
        Keypoint(name=str(p["name"]), x=float(p["x"]), y=float(p["y"]))
        for p in (entry.get("keypoints") or [])
        if isinstance(p, dict) and {"name", "x", "y"} <= set(p)
    ]
    category: GarmentCategory = entry["category"]  # type: ignore[assignment]
    return {
        "id": entry["id"],
        "name": entry["name"],
        "dynasty": entry.get("dynasty", "未知"),
        "category": category,
        "tags": list(entry.get("tags") or []),
        "image_url": static_url(entry["image"]),
        "thumb_url": static_url(thumb),
        "keypoints": keypoints,
        "source_text": entry.get("source_text", ""),
        "references": list(entry.get("references") or []),
    }


def load_asset(gid: str) -> GarmentAsset:
    """按 id 从磁盘加载素材（图 + 掩码 + 关键点）。"""
    from app.utils.imageio import load_rgb, load_rgb_with_alpha, normalize_mask, resize_mask

    for entry in load_index():
        if entry.get("id") != gid:
            continue
        root = _asset_root()
        image_file = entry["image"]
        # index.json 中的路径约定为 data/garments/xxx.png（相对 data/ 目录）
        image_path = (root.parent / image_file).resolve()
        if not image_path.is_file():
            raise GarmentNotFoundError(f"素材图片文件缺失：{image_file}")
        image, alpha = load_rgb_with_alpha(image_path.read_bytes(), label="服饰图")

        mask_file = entry.get("mask")
        if mask_file:
            mask_path = (root.parent / mask_file).resolve()
            if mask_path.is_file():
                mask = normalize_mask(np.asarray(load_rgb(mask_path.read_bytes())[:, :, 0]))
                if mask.shape[:2] != image.shape[:2]:
                    mask = resize_mask(mask, image.shape[0], image.shape[1])
            elif alpha is not None:
                mask = normalize_mask(alpha)
            else:
                mask = np.full(image.shape[:2], 255, dtype=np.uint8)
        elif alpha is not None:
            # 无独立掩码时，直接用素材自带透明通道作为服饰前景掩码
            mask = normalize_mask(alpha)
        else:
            mask = np.full(image.shape[:2], 255, dtype=np.uint8)

        keypoints = {
            str(p["name"]): (float(p["x"]), float(p["y"]))
            for p in entry.get("keypoints") or []
            if isinstance(p, dict)
        }
        return GarmentAsset(
            id=gid,
            name=entry["name"],
            dynasty=entry.get("dynasty", "未知"),
            category=entry["category"],
            tags=list(entry.get("tags") or []),
            image=image,
            mask=mask,
            keypoints=keypoints,
            source_text=entry.get("source_text", ""),
            references=list(entry.get("references") or []),
        )
    raise GarmentNotFoundError()


def asset_from_bytes(raw: bytes, *, gid: str = "adhoc", name: str = "临时上传服饰") -> GarmentAsset:
    """用户直接上传的服饰图（无预标注）：自动抠前景 + 自动推导 9 关键点。"""
    from app.services.garments.auto_annotate import infer_keypoints_from_mask
    from app.utils.cv import keep_largest_component
    from app.utils.imageio import load_rgb_with_alpha, normalize_mask

    image, alpha = load_rgb_with_alpha(raw, label="服饰图")
    if alpha is not None:
        mask = normalize_mask(alpha)
    else:
        # 无透明通道：用「中心先验 ∩ 颜色显著性」近似抠出服饰前景
        from app.services.segmentation.heuristic import _center_prior_mask, _color_salience

        mask = normalize_mask(np.minimum(_center_prior_mask(image.shape), _color_salience(image)))
        mask = keep_largest_component(mask)
    if int((mask > 127).sum()) < 256:
        raise GarmentNotFoundError("服饰图未能分离出前景，请上传抠好的透明背景 PNG")

    keypoints = infer_keypoints_from_mask(mask)
    return GarmentAsset(
        id=gid,
        name=name,
        dynasty="自定义",
        category="top",
        tags=["adhoc"],
        image=image,
        mask=mask,
        keypoints=keypoints,
        source_text="用户上传的临时服饰图，关键点由掩码自动推导。",
        references=[],
    )


def trace_card_for(gid: str) -> TraceCard:
    for entry in load_index():
        if entry.get("id") == gid:
            return TraceCard(
                garment_id=gid,
                name=entry.get("name", gid),
                dynasty=entry.get("dynasty", "未知"),
                category=entry.get("category", "top"),
                source_text=entry.get("source_text", ""),
                references=list(entry.get("references") or []),
            )
    raise GarmentNotFoundError()


__all__ = [
    "REQUIRED_KEYPOINTS",
    "GarmentAsset",
    "asset_from_bytes",
    "bbox_area_ratio",
    "entry_to_output",
    "load_asset",
    "load_index",
    "static_url",
    "to_db_payload",
    "trace_card_for",
    "valid_entries",
    "validate_entry",
]
