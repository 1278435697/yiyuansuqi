"""环境体检：打印依赖 / Provider 可用矩阵，可选端到端自检。

用法：
    python -m scripts.doctor              # 只打印可用性矩阵
    python -m scripts.doctor --selftest    # 用示例人像真跑一遍流水线（无 GPU 也应出图）
"""

from __future__ import annotations

import argparse
import asyncio
import platform
import sys

from scripts._bootstrap import bootstrap

bootstrap()

_SYMBOL = {True: "✔", False: "✘"}


def _fmt(ok: bool) -> str:
    return _SYMBOL[bool(ok)]


def _print_matrix() -> dict:
    from app.config import get_settings
    from app.services import pose, segmentation, vton
    from app.services.garments import load_index, valid_entries
    from app.utils.cv import cv_available

    settings = get_settings()
    print("=" * 68)
    print(f"衣溯AI 体检 | Python {platform.python_version()} | {platform.platform()}")
    print(f"数据目录 {settings.data_dir}")
    print(f"权重目录 {settings.weights_dir}")
    print(f"推理后端配置 YISU_VTON_BACKEND={settings.vton_backend} | force_cpu={settings.force_cpu}")
    print("=" * 68)

    matrix: dict[str, list[tuple[str, bool, str]]] = {}

    seg_rows = []
    for name, info in segmentation.status().items():
        seg_rows.append((name, info["available"], str(info.get("reason") or "")))
    matrix["分割 Provider（按优先级）"] = seg_rows

    pose_rows = []
    for name, info in pose.status().items():
        pose_rows.append((name, info["available"], f"{info.get('mode') or ''} {info.get('reason') or ''}".strip()))
    matrix["姿态 Provider"] = pose_rows

    vton_rows = []
    for name, info in vton.status().items():
        if name == "resolved_auto":
            continue
        vton_rows.append((name, info["available"], str(info.get("reason") or "")))
    matrix["试穿推理后端（按优先级）"] = vton_rows

    backend, fallback = vton.resolve("auto")
    env_rows = [
        ("numpy/scipy", True, ""),
        ("Pillow", True, ""),
        ("OpenCV", cv_available()[0], cv_available()[1] or ""),
        ("torch", _has("torch"), ""),
        ("CUDA", _cuda_available(), "未检测到可用 GPU（不影响 TPS 兜底）"),
        ("onnxruntime", _has("onnxruntime"), ""),
        ("mediapipe", _has("mediapipe"), ""),
    ]
    matrix["依赖库"] = env_rows

    weight_rows = [
        ("gcpait_vitongpu_2k.onnx", _exists(settings.vitongpu_onnx), ""),
        ("u2net.onnx / u2netp.onnx", _u2net_ready(settings), ""),
        ("hrviton 权重目录", bool(settings.hrviton_ckpt_dir and settings.hrviton_ckpt_dir.is_dir()), ""),
    ]
    matrix["可选权重"] = weight_rows

    try:
        entries, skipped = valid_entries(load_index())
    except Exception as exc:  # noqa: BLE001
        entries, skipped = [], [str(exc)]
    matrix["素材库"] = [
        (f"index.json 可用素材 {len(entries)} 件", bool(entries), "请先运行 python -m scripts.gen_sample_garments" if not entries else ""),
        (f"校验跳过 {len(skipped)} 条", True, "; ".join(skipped[:3])),
    ]

    for title, rows in matrix.items():
        print(f"\n[{title}]")
        for name, ok, reason in rows:
            line = f"  {_fmt(ok)} {name:<28}"
            if reason:
                line += f" — {reason[:72]}"
            print(line)

    print("\n" + "-" * 68)
    print(f"最终选定后端：{getattr(backend, 'name', 'unknown')}")
    if fallback:
        print(f"降级原因：{fallback}")
    print("说明：TPS 兜底路径零权重、纯 CPU，任何机器都应能出图；"
          "装上 mediapipe / u2net 权重后会自动升级为更精确的分割与姿态。")
    return {"backend": getattr(backend, "name", "unknown"), "entries": len(entries)}


def _has(module: str) -> bool:
    import importlib.util

    try:
        return importlib.util.find_spec(module) is not None
    except (ImportError, ValueError):  # pragma: no cover
        return False


def _cuda_available() -> bool:
    from app.config import get_settings

    if get_settings().force_cpu:
        return False
    try:
        import torch
    except Exception:  # noqa: BLE001
        return False
    return bool(torch.cuda.is_available())


def _u2net_ready(settings) -> bool:
    if not settings.u2net_onnx:
        return False
    return any(
        p.is_file() for p in (settings.u2net_onnx, settings.u2net_onnx.with_name("u2netp.onnx"))
    )


def _exists(path) -> bool:
    return bool(path and path.is_file())


async def _selftest() -> int:
    """真实跑一遍流水线：优先使用示例人像，否则用生成图。"""
    import numpy as np

    from app.config import get_settings
    from app.services.garments import load_asset
    from app.services.pipeline import run_tryon
    from app.utils.imageio import load_rgb
    from scripts.gen_sample_garments import render_sample_person

    settings = get_settings()
    samples = settings.data_dir / "samples"
    # 与前端「使用示例人像」一致：真实人像优先，缺失才回落到示意图
    person_path = next(
        (p for p in (samples / "person_real.png", samples / "person_demo.png") if p.is_file()),
        None,
    )
    if person_path is None:
        render_sample_person(settings.data_dir)
        person_path = samples / "person_demo.png"
    person_rgb = load_rgb(person_path.read_bytes(), label="示例人像")

    from app.services.garments import load_index, valid_entries

    entries, _ = valid_entries(load_index())
    if not entries:
        print("[selftest] 无可用素材，请先运行 python -m scripts.gen_sample_garments")
        return 1
    gid = entries[0]["id"]
    garment = load_asset(gid)

    task_id = f"doctor_{np.random.default_rng().integers(0, 9999):04d}"
    out = run_tryon(task_id=task_id, person_rgb=person_rgb, garment=garment, quality="fast")
    result_path = settings.results_dir / task_id / "result.jpg"
    print(f"\n[selftest] 素材={gid} 人像={person_path.name} 后端={out.backend_used} 结果图={result_path}")
    print(f"[selftest] 耗时={out.timings}")
    if out.warnings:
        print(f"[selftest] warnings={out.warnings}")
    if not result_path.is_file():
        print("[selftest] 失败：结果图未落盘")
        return 1
    print(f"[selftest] 中间图目录：{settings.results_dir / task_id}")
    print("[selftest] 通过 ✅ 端到端出图成功")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="环境与流水线体检")
    parser.add_argument("--selftest", action="store_true", help="用示例人像端到端跑一次试穿")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出摘要（供脚本消费）")
    args = parser.parse_args()

    info = _print_matrix()
    if args.json:
        import json

        print(json.dumps(info, ensure_ascii=False))
    rc = 0
    if args.selftest:
        try:
            rc = asyncio.run(_selftest())
        except Exception as exc:  # noqa: BLE001
            print(f"[selftest] 异常：{type(exc).__name__}: {exc}", file=sys.stderr)
            rc = 1
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
