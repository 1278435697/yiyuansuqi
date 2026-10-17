"""把「真实照片素材」接进素材库：自动抠图 + 自动标 9 关键点 + 生成缩略图 + upsert index.json。

解决的是「示例素材是程序化色块图，看起来不像真衣服」这个问题。给它一张白底/透明底的
汉服照片（商品图、馆藏翻拍图、AI 生成图皆可），它会产出与 gen_sample_garments 完全同构的
`{id}.png / {id}_mask.png / {id}_thumb.png` 与 keypoints，因此 TPS/HR-VITON/前端全都无需改动。

用法：
    # 单件（id 已存在时只替换图片，保留原有名称/朝代/史料文本）
    python -m scripts.register_garments --image C:\\path\\quju.png --id quju-shenyi

    # 一批（manifest 见 --print-manifest）
    python -m scripts.register_garments --manifest data/garments/real_manifest.json

    # 顺带换掉示例人像（前端「使用示例人像」会优先取 person_real.png）
    python -m scripts.register_garments --manifest ... --person C:\\path\\model.png

    # 注册后立即用真实人像出一张预览图，肉眼确认效果
    python -m scripts.register_garments --manifest ... --preview
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts._bootstrap import bootstrap

bootstrap()

_THUMB_LONG_SIDE = 256
_BBOX_MARGIN = 0.06


def _print_manifest_help() -> int:
    template = {
        "garments": [
            {
                "id": "quju-shenyi",
                "image": "C:/path/quju.png",
                "name": "曲裾深衣",
                "dynasty": "汉代",
                "category": "robe",
                "tags": ["曲裾", "绕襟", "丝"],
                "source_text": "可选；缺省时沿用 index.json 中原有条目",
                "references": ["可选"],
            }
        ]
    }
    print(json.dumps(template, ensure_ascii=False, indent=2))
    return 0


def _load_index(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {"version": 1, "garments": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {"version": 1, "garments": data}
    data.setdefault("garments", [])
    return data


def _crop_to_content(rgb, mask):
    """按掩码包围盒裁剪并留边距：让服饰尽量填满画框，形变时分辨率利用率更高。"""
    import numpy as np

    ys, xs = np.where(mask > 127)
    if ys.size == 0:
        return rgb, mask
    h, w = mask.shape
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    pad_y = int((bottom - top) * _BBOX_MARGIN) or 4
    pad_x = int((right - left) * _BBOX_MARGIN) or 4
    y0, y1 = max(0, top - pad_y), min(h, bottom + pad_y + 1)
    x0, x1 = max(0, left - pad_x), min(w, right + pad_x + 1)
    return rgb[y0:y1, x0:x1].copy(), mask[y0:y1, x0:x1].copy()


def _resolve_mask(rgb, alpha, *, force_salience: bool):
    """优先用透明通道；否则纯色底抠图；再退到「中心先验 ∩ 颜色显著性」。"""
    import numpy as np

    from app.services.garments.matting import cutout_solid_background, is_solid_background
    from app.utils.cv import keep_largest_component
    from app.utils.imageio import normalize_mask

    if alpha is not None and not force_salience:
        # AI 生成图与翻拍图常自带一条「几乎全不透明」的 alpha，信它等于把整帧当服饰：
        # 掩码铺满、裁剪失效、关键点落到画框四角，而 validate_entry 仍会放行。
        # 只有确实存在透明底（不透明占比 < 97%）才把 alpha 当抠图结果。
        opaque_ratio = float((alpha > 127).mean())
        if 256 < int((alpha > 127).sum()) and opaque_ratio < 0.97:
            return normalize_mask(alpha), "alpha"
    if is_solid_background(rgb) or force_salience:
        mask = cutout_solid_background(rgb)
        if int((mask > 127).sum()) > 256:
            return mask, "matting"
    from app.services.segmentation.heuristic import _center_prior_mask, _color_salience

    mask = normalize_mask(np.minimum(_center_prior_mask(rgb.shape), _color_salience(rgb)))
    return keep_largest_component(mask), "heuristic"


def register_one(item: dict[str, Any], *, garments_dir: Path, index: dict[str, Any], long_side: int,
                 force_salience: bool) -> dict[str, Any]:
    import numpy as np

    from app.services.garments.auto_annotate import keypoints_for_category, keypoints_to_list
    from app.utils.imageio import load_rgb_with_alpha, save_png
    from app.utils.imageio import shrink_to_long_side

    gid = str(item.get("id", "")).strip()
    if not gid:
        raise ValueError("条目缺少 id")
    source = Path(str(item.get("image", ""))).expanduser()
    if not source.is_file():
        raise FileNotFoundError(f"源图片不存在：{source}")

    raw = source.read_bytes()
    rgb, alpha = load_rgb_with_alpha(raw, label="服饰图")
    import io

    from PIL import Image

    shrunk = shrink_to_long_side(Image.open(io.BytesIO(raw)), long_side)
    if shrunk.size != (rgb.shape[1], rgb.shape[0]):
        rgb = np.asarray(shrunk.convert("RGB"), dtype=np.uint8)
        if alpha is not None:
            alpha = np.asarray(
                Image.fromarray(alpha, mode="L").resize(shrunk.size, Image.BILINEAR), dtype=np.uint8
            )

    mask, how = _resolve_mask(rgb, alpha, force_salience=force_salience)
    if int((mask > 127).sum()) < 256:
        raise ValueError(f"{gid}: 未能分离服饰前景（可加 --force-salience 或改透明底 PNG）")
    coverage = float((mask > 127).mean())
    if coverage > 0.92:
        raise ValueError(f"{gid}: 掩码覆盖了 {coverage:.0%} 画面，等于没抠图（换 --force-salience 或换素材图）")
    rgb, mask = _crop_to_content(rgb, mask)

    category = str(item.get("category") or "").strip()
    existing = next((g for g in index["garments"] if g.get("id") == gid), None)
    category = category or (existing or {}).get("category") or "top"

    keypoints = keypoints_for_category(mask, category)

    save_png(rgb, garments_dir / f"{gid}.png")
    save_png(mask, garments_dir / f"{gid}_mask.png")
    thumb = np.asarray(
        Image.fromarray(rgb).resize(
            (
                max(1, int(round(rgb.shape[1] * _THUMB_LONG_SIDE / max(rgb.shape[:2])))),
                max(1, int(round(rgb.shape[0] * _THUMB_LONG_SIDE / max(rgb.shape[:2])))),
            ),
            Image.LANCZOS,
        ),
        dtype=np.uint8,
    )
    save_png(thumb, garments_dir / f"{gid}_thumb.png")

    entry = {
        "id": gid,
        "name": item.get("name") or (existing or {}).get("name") or gid,
        "dynasty": item.get("dynasty") or (existing or {}).get("dynasty") or "未知",
        "category": category,
        "tags": item.get("tags") or (existing or {}).get("tags") or [],
        "image": f"garments/{gid}.png",
        "mask": f"garments/{gid}_mask.png",
        "thumb": f"garments/{gid}_thumb.png",
        "keypoints": keypoints_to_list(keypoints),
        "source_text": item.get("source_text")
        if "source_text" in item
        else (existing or {}).get("source_text", ""),
        "references": item.get("references")
        if "references" in item
        else (existing or {}).get("references", []),
    }
    if existing is not None:
        index["garments"] = [entry if g.get("id") == gid else g for g in index["garments"]]
    else:
        index["garments"].append(entry)
    print(f"  ✔ {gid:<16} {rgb.shape[1]}x{rgb.shape[0]}  抠图={how}  关键点={len(entry['keypoints'])}")
    return entry


def _install_person(path: Path, *, data_dir: Path, long_side: int) -> Path:
    import io

    import numpy as np
    from PIL import Image

    from app.utils.imageio import load_rgb, save_png, shrink_to_long_side

    raw = path.read_bytes()
    rgb = load_rgb(raw, label="人像图")
    shrunk = shrink_to_long_side(Image.open(io.BytesIO(raw)), long_side)
    if shrunk.size != (rgb.shape[1], rgb.shape[0]):
        rgb = np.asarray(shrunk.convert("RGB"), dtype=np.uint8)
    target = data_dir / "samples" / "person_real.png"
    target.parent.mkdir(parents=True, exist_ok=True)
    save_png(rgb, target)
    print(f"  ✔ 示例人像 → {target.relative_to(data_dir.parent)}（{rgb.shape[1]}x{rgb.shape[0]}）")
    return target


def _preview(gid: str, *, data_dir: Path) -> Path | None:
    """注册后立即跑一次真实合成，产出可直接肉眼检查的预览图。"""
    from app.services.garments import load_asset
    from app.services.pipeline import run_tryon
    from app.utils.imageio import load_rgb

    person_path = data_dir / "samples" / "person_real.png"
    if not person_path.is_file():
        person_path = data_dir / "samples" / "person_demo.png"
    if not person_path.is_file():
        print("  ⚠ 无示例人像，跳过预览（可加 --person 指定）")
        return None
    out_dir = data_dir / "results" / f"preview_{gid}"
    out = run_tryon(
        task_id=out_dir.name,
        person_rgb=load_rgb(person_path.read_bytes(), label="人像图"),
        garment=load_asset(gid),
        quality="hd",
    )
    result = out_dir / "result.jpg"
    print(f"  → 预览 {result}  后端={out.backend_used} 耗时={out.timings.get('total')}s")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="真实服饰照片 → 素材库（自动抠图 + 自动标注）")
    parser.add_argument("--image", help="单件模式：源图片路径")
    parser.add_argument("--id", dest="gid", help="单件模式：素材 id（与 index.json 中已有 id 相同即替换）")
    parser.add_argument("--name", default=None)
    parser.add_argument("--dynasty", default=None)
    parser.add_argument("--category", default=None, choices=[None, "top", "dress", "skirt", "robe"])
    parser.add_argument("--tags", default=None, help="逗号分隔")
    parser.add_argument("--manifest", help="批量模式：JSON 清单（见 --print-manifest）")
    parser.add_argument("--person", default=None, help="真实示例人像图片路径（可单独使用，只换人像不注册服饰）")
    parser.add_argument("--data-dir", default=None, help="默认 backend/data")
    parser.add_argument("--long-side", type=int, default=1024)
    parser.add_argument("--force-salience", action="store_true", help="跳过透明通道，强制按颜色显著性抠图")
    parser.add_argument("--preview", action="store_true", help="注册后立刻用示例人像出图验证")
    parser.add_argument("--seed", action="store_true", help="注册后直接 upsert 入数据库")
    parser.add_argument("--print-manifest", action="store_true", help="打印清单模板后退出")
    args = parser.parse_args(argv)

    if args.print_manifest:
        return _print_manifest_help()

    items: list[dict[str, Any]] = []
    if args.manifest:
        manifest_path = Path(args.manifest).expanduser()
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        items = list(payload.get("garments") or [])
        person_arg = payload.get("person") or args.person
    elif args.image and args.gid:
        items = [
            {
                "id": args.gid,
                "image": args.image,
                "name": args.name,
                "dynasty": args.dynasty,
                "category": args.category,
                "tags": [t.strip() for t in (args.tags or "").split(",") if t.strip()],
            }
        ]
        person_arg = args.person
    elif args.person:
        # 只换示例人像，不动素材库
        person_arg = args.person
    else:
        parser.error("需要 --manifest、--person 或（--image 且 --id）")
        return 2

    from app.config import get_settings
    from app.services.garments import validate_entry

    settings = get_settings()
    data_dir = Path(args.data_dir).expanduser().resolve() if args.data_dir else settings.data_dir
    garments_dir = data_dir / "garments"
    garments_dir.mkdir(parents=True, exist_ok=True)
    index_path = garments_dir / "index.json"
    index = _load_index(index_path)

    print(f"数据目录：{data_dir}")
    if person_arg:
        _install_person(Path(person_arg).expanduser(), data_dir=data_dir, long_side=args.long_side)

    registered: list[str] = []
    for item in items:
        try:
            entry = register_one(
                item,
                garments_dir=garments_dir,
                index=index,
                long_side=args.long_side,
                force_salience=args.force_salience,
            )
        except Exception as exc:  # noqa: BLE001 - 单件失败不影响其余素材
            print(f"  ✘ {item.get('id', '?')}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        ok, reason, ratio = validate_entry(entry)
        if not ok:
            print(f"  ⚠ {entry['id']} 校验未通过：{reason}（面积比 {ratio:.3f}）", file=sys.stderr)
        else:
            registered.append(entry["id"])

    if not registered:
        if not items:
            print("仅更新示例人像，index.json 未改动。")
            return 0
        print("没有素材注册成功，index.json 未改动。", file=sys.stderr)
        return 1

    index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"index.json 已更新（写入 {len(registered)} 件：{registered}）")

    if args.seed:
        import asyncio

        from app.services.seed import seed_garments

        # 刚重注册的素材 keypoints/缩略图都变了，必须 force 覆盖，否则库里仍是旧几何
        written, skipped = asyncio.run(seed_garments(force=True))
        print(f"数据库种子：写入/更新 {written} 条，跳过 {len(skipped)} 条")

    if args.preview:
        for gid in registered:
            _preview(gid, data_dir=data_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
