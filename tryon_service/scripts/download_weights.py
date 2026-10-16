"""可选模型权重下载器（带主机白名单、断点续传、SHA256 校验、原子落盘）。

原则：
1. 只从白名单域名直连下载，任何重定向目标也必须在白名单内；
2. 先写 `<file>.part` 续传，校验通过后原子 rename，避免半个权重污染 Provider 探测；
3. 官方不直发权重的项目（HR-VITON、VitonGPCI）只打印获取指引，不硬编码来源不明的链接；
4. SHA256 缺省不校验（上游未公布固定校验值），可用 --sha256 或 YISU_SHA256_<ASSET> 强制校验。

用法：
    python -m scripts.download_weights --list
    python -m scripts.download_weights --asset u2net
    python -m scripts.download_weights --asset vitongpu --url https://<白名单内直链>
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

from scripts._bootstrap import bootstrap

bootstrap()

ALLOWED_HOSTS = (
    "github.com",
    "objects.githubusercontent.com",
    "release-assets.githubusercontent.com",
    "huggingface.co",
    "cdn-lfs.huggingface.co",
    "cdn-lfs-us-1.huggingface.co",
    "storage.googleapis.com",
)

# asset -> 目标文件与候选直链（候选顺序即尝试顺序）
ASSETS: dict[str, dict] = {
    "u2net": {
        "filename": "u2net.onnx",
        "urls": [
            "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx",
            "https://huggingface.co/twoned/tryon/resolve/main/u2net.onnx",
        ],
        "note": "U2Net 人像/通用 saliency，约 170MB；失败可改 --asset u2netp（4MB）",
    },
    "u2netp": {
        "filename": "u2netp.onnx",
        "urls": [
            "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx",
        ],
        "note": "U2Netp 轻量版，CPU 上更快、精度略低",
    },
    "vitongpu": {
        "filename": "gcpait_vitongpu_2k.onnx",
        "urls": [],
        "manual": (
            "VitonGPCI 语义解析权重（gcpait_vitongpu_2k.onnx）由论文项目页发布，"
            "请从 https://github.com/VitonGPCI/VitonGPCI 给出的官方下载链接取得，"
            "再用 --url 传入直链，或直接把文件放到 weights/ 下。"
        ),
        "note": "18 类人体语义解析，能同时给出 clothes/arm/head 区域（最优分割 Provider）",
    },
    "hrviton": {
        "filename": None,
        "urls": [],
        "manual": (
            "HR-VITON 官方不直接发布权重，需按 https://github.com/sangyun884/HR-VITON "
            "README 中的表单/网盘链接获取 mtviton_step_100000.pth 与 gen_step_110000.pth，"
            "放入 weights/hrviton/。Google Drive 链接可用 `pip install gdown` 后：\n"
            "  gdown --fuzzy <分享链接> -O weights/hrviton/<文件名>\n"
            "同时需 git clone 仓库并设置环境变量 YISU_HRVITON_REPO。"
        ),
        "note": "高精度后端，需 NVIDIA GPU + CUDA；缺失时自动降级 TPS",
    },
    "pose_landmarker": {
        "filename": "pose_landmarker_full.task",
        "urls": [
            "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
            "pose_landmarker_full/float16/latest/pose_landmarker_full.task",
        ],
        "note": "MediaPipe Tasks 姿态模型（可选；未提供时使用 pip 包内置 solutions 模型）",
    },
}


def _sha256(path: Path, chunk: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def _host_allowed(url: str) -> bool:
    host = (urlparse(url).netloc or "").lower()
    return any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_HOSTS)


def _http_get(url: str, part: Path, *, timeout: tuple[int, int] = (5, 30)) -> None:
    """断点续传下载：Range 请求 → 追加写。"""
    import requests

    existing = part.stat().st_size if part.exists() else 0
    headers = {"Range": f"bytes={existing}-"} if existing else {}
    mode = "ab" if existing else "wb"
    print(f"[download] {url}")
    if existing:
        print(f"[download] 续传，已存在 {existing / 1024 / 1024:.1f}MB")

    with requests.get(url, headers=headers, stream=True, timeout=timeout, allow_redirects=True) as resp:
        if resp.status_code == 416:  # 已下完
            return
        if resp.status_code not in (200, 206):
            raise RuntimeError(f"HTTP {resp.status_code}")
        if existing and resp.status_code == 200:
            # 服务器不支持 Range，回到从头下载
            mode, existing = "wb", 0
        total = int(resp.headers.get("content-length") or 0) + existing
        done = existing
        bar_step = max(1, int(8 * 1024 * 1024))
        next_mark = done + bar_step
        with part.open(mode) as handle:
            for chunk in resp.iter_content(chunk_size=1024 * 512):
                if not chunk:
                    continue
                handle.write(chunk)
                done += len(chunk)
                if done >= next_mark and total:
                    print(f"[download]   {done / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f}MB")
                    next_mark += bar_step
    print(f"[download] 完成 {done / 1024 / 1024:.1f}MB")


def fetch(asset: str, dest_dir: Path, *, url: str | None, sha256: str | None) -> int:
    meta = ASSETS[asset]
    filename = meta["filename"]
    if filename is None:
        print(f"[{asset}] 该权重不提供自动下载：\n{meta['manual']}")
        return 2

    target = dest_dir / filename
    if target.exists():
        print(f"[{asset}] 已存在：{target}（{target.stat().st_size / 1024 / 1024:.1f}MB），跳过")
        return 0

    candidates = [url] if url else list(meta.get("urls") or [])
    candidates = [c for c in candidates if c]
    if not candidates:
        print(f"[{asset}] 没有可用直链。{meta.get('manual', '')}")
        print(f"        可执行：python -m scripts.download_weights --asset {asset} --url <官方直链>")
        return 2

    dest_dir.mkdir(parents=True, exist_ok=True)
    expected = sha256 or os.environ.get(f"YISU_SHA256_{asset.upper()}", "") or None

    for candidate in candidates:
        if not candidate.startswith(("http://", "https://")):
            print(f"[{asset}] 忽略非法 URL（必须是 http/https）：{candidate}")
            continue
        if not _host_allowed(candidate):
            print(f"[{asset}] 拒绝非白名单主机：{urlparse(candidate).netloc}（ALLOWED_HOSTS 可自助扩展）")
            continue
        part = target.with_suffix(target.suffix + ".part")
        try:
            _http_get(candidate, part)
        except Exception as exc:  # noqa: BLE001 - 逐个候选源尝试
            print(f"[{asset}] 下载失败：{type(exc).__name__}: {exc}")
            if part.exists() and part.stat().st_size == 0:
                part.unlink(missing_ok=True)
            continue

        actual = _sha256(part)
        print(f"[{asset}] SHA256={actual}")
        if expected and actual != expected.lower():
            print(f"[{asset}] 校验不匹配（期望 {expected}），删除损坏文件后换源")
            part.unlink(missing_ok=True)
            continue

        if not expected:
            print(f"[{asset}] 未提供期望 SHA256，仅按大小合理性检查")
            if part.stat().st_size < 64 * 1024:
                print(f"[{asset}] 文件过小，判定为无效权重（可能是 HTML 错误页），删除")
                part.unlink(missing_ok=True)
                continue

        os.replace(part, target)  # 原子 rename
        print(f"[{asset}] 已写入 {target}")
        return 0

    print(f"[{asset}] 所有候选源均失败；请手动下载后放到 {dest_dir}")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="可选模型权重下载器")
    parser.add_argument("--asset", default="all", help=f"{', '.join(ASSETS)} 或 all")
    parser.add_argument("--dest", default=None, help="保存目录，默认 backend/weights")
    parser.add_argument("--url", default=None, help="覆盖候选直链（仍受白名单约束）")
    parser.add_argument("--sha256", default=None, help="期望 SHA256，可省")
    parser.add_argument("--list", action="store_true", dest="show_list", help="列出全部资产")
    args = parser.parse_args()

    from app.config import get_settings

    dest = Path(args.dest).resolve() if args.dest else get_settings().weights_dir

    if args.show_list:
        print(f"保存目录：{dest}\n白名单主机：{', '.join(ALLOWED_HOSTS)}")
        for name, meta in ASSETS.items():
            ready = (
                "n/a"
                if meta["filename"] is None
                else ("已下载" if (dest / meta["filename"]).exists() else "缺失")
            )
            print(f"- {name:<15} {meta['filename'] or '(多文件/手动)':<32} {ready:<8} {meta['note']}")
            if meta.get("manual"):
                print("  " + meta["manual"].replace("\n", "\n  "))
        return 0

    names = list(ASSETS) if args.asset == "all" else [args.asset]
    if args.asset != "all" and args.asset not in ASSETS:
        print(f"未知 asset：{args.asset}（可选：{', '.join(ASSETS)}）", file=sys.stderr)
        return 2

    rc = 0
    for name in names:
        print(f"\n=== {name} ===")
        rc = max(rc, fetch(name, dest, url=args.url, sha256=args.sha256))
    if rc == 0:
        print("\n提示：运行 python -m scripts.doctor 查看 Provider 是否已自动升级")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
