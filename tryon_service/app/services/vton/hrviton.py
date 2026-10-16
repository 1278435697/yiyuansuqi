"""高精度试穿后端：调用本地 HR-VITON 工程（需 GPU + 官方权重 + 已克隆仓库）。

设计要点：不在本仓库内复刻 HR-VITON 的网络结构与超参（权重官方不直发、
结构随分叉版本变化），而是以「外部命令模板」方式调用已克隆的 HR-VITON 推理入口，
这样不同分叉（sangyun884/HR-VITON、cedro3/HR-VITON）都能通过配置接入。

启用条件（全部满足才 available）：
1. torch 可导入且 CUDA 可用（或显式 YISU_HRVITON_ALLOW_CPU=1）；
2. weights/hrviton/ 下存在 mtviton_step_100000.pth 与 gen_step_110000.pth；
3. 配置了 hrviton_repo_dir（环境变量 YISU_HRVITON_REPO）且该目录存在推理入口脚本；
4. 命令模板 hrviton_command 可格式化执行。

任一条件不满足 → 返回明确原因，由 vton.resolve 降级到 TPS，绝不静默失败。
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.errors import TryOnFailedError
from app.logs import get_logger
from app.services.vton.base import TryOnContext, TryOnOutput
from app.utils.imageio import save_png

logger = get_logger("app.services.vton.hrviton")

WEIGHT_FILES = ("mtviton_step_100000.pth", "gen_step_110000.pth")
ENTRY_HINTS = ("inference.py", "test_hrvt.py", "hrvt_test.py", "test.py")
_TIMEOUT_SECONDS = 180


class HRVITONBackend:
    name = "hrviton"

    def __init__(self) -> None:
        self._probed = False
        self._ok = False
        self._reason: str | None = None

    # ---------- 探测 ----------
    @staticmethod
    def _weights_ready() -> tuple[bool, str | None]:
        ckpt_dir = get_settings().hrviton_ckpt_dir
        missing = [f for f in WEIGHT_FILES if not (ckpt_dir / f).is_file()]
        if missing:
            return False, (
                f"缺少 HR-VITON 权重 {missing}（目录 {ckpt_dir}），"
                "可运行 scripts/download_weights.py --asset hrviton"
            )
        return True, None

    @staticmethod
    def _repo_ready() -> tuple[Path | None, str | None]:
        repo = Path(os.environ.get("YISU_HRVITON_REPO", "backend/third_party/HR-VITON"))
        if not repo.is_absolute():
            repo = (Path(__file__).resolve().parents[3] / ".." / repo).resolve()
        if not repo.is_dir():
            return None, f"未克隆 HR-VITON 仓库或路径错误：{repo}（git clone https://github.com/sangyun884/HR-VITON 后设置 YISU_HRVITON_REPO）"
        if not any((repo / hint).is_file() for hint in ENTRY_HINTS):
            return None, f"仓库 {repo.name} 内未找到推理入口脚本（{', '.join(ENTRY_HINTS)}）"
        return repo, None

    def available(self) -> tuple[bool, str | None]:
        if self._probed:
            return self._ok, self._reason
        self._probed = True
        settings = get_settings()
        try:
            import torch
        except Exception as exc:  # noqa: BLE001
            self._reason = f"torch 未安装：{exc}"
            return False, self._reason
        if settings.force_cpu or not torch.cuda.is_available():
            if os.environ.get("YISU_HRVITON_ALLOW_CPU", "0") != "1":
                self._reason = "未检测到可用 CUDA（HR-VITON 推理需要 GPU；如需 CPU 试跑请设置 YISU_HRVITON_ALLOW_CPU=1）"
                return False, self._reason
        ok, reason = self._weights_ready()
        if not ok:
            self._reason = reason
            return False, reason
        repo, reason = self._repo_ready()
        if repo is None:
            self._reason = reason
            return False, reason
        if not settings.hrviton_command.strip():
            self._reason = "未配置 YISU_HRVITON_COMMAND 命令模板"
            return False, self._reason
        self._ok = True
        logger.info("HR-VITON 后端就绪（repo=%s）", repo.name)
        return True, None

    # ---------- 执行 ----------
    def run(self, ctx: TryOnContext) -> TryOnOutput:
        ok, reason = self.available()
        if not ok:
            raise TryOnFailedError(detail=reason or "HR-VITON 不可用")

        settings = get_settings()
        repo, _ = self._repo_ready()
        assert repo is not None
        workdir = (settings.results_dir / f"hrviton_{int(time.time() * 1000)}").resolve()
        workdir.mkdir(parents=True, exist_ok=True)
        try:
            person_path = save_png(ctx.person_rgb, workdir / "person.png")
            garment_path = save_png(ctx.garment.image, workdir / "garment.png")
            out_dir = workdir / "out"
            out_dir.mkdir(parents=True, exist_ok=True)

            command = settings.hrviton_command.format(
                person=str(person_path),
                garment=str(garment_path),
                out_dir=str(out_dir),
                repo=str(repo),
                weights=str(settings.hrviton_ckpt_dir),
                resolution="512" if ctx.quality == "hd" else "256",
            )
            logger.info("执行 HR-VITON 推理命令: %s", command)
            completed = subprocess.run(  # noqa: S602 - 由运维配置的可信命令模板
                command,
                shell=True,
                cwd=str(repo),
                capture_output=True,
                text=True,
                timeout=_TIMEOUT_SECONDS,
            )
            if completed.returncode != 0:
                tail = (completed.stderr or completed.stdout or "")[-800:]
                raise TryOnFailedError(detail=f"HR-VITON 退出码 {completed.returncode}: {tail}")

            produced = sorted(
                (p for p in out_dir.rglob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg"}),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if not produced:
                raise TryOnFailedError(detail="HR-VITON 未产出结果图，请检查命令模板输出目录约定")

            from app.utils.imageio import load_rgb

            result = load_rgb(produced[0].read_bytes(), label="HR-VITON 结果图")
            if result.shape[:2] != ctx.shape:
                result = _resize_to(result, ctx.shape)
            return TryOnOutput(
                result=result,
                warped_rgb=None,
                warped_mask=None,
                warp_window=None,
                backend=self.name,
                notes=[f"entry={produced[0].name}", f"repo={repo.name}"],
            )
        finally:
            shutil.rmtree(workdir, ignore_errors=True)


def _resize_to(rgb: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    from PIL import Image

    return np.asarray(
        Image.fromarray(rgb).resize((shape[1], shape[0]), Image.BILINEAR), dtype=np.uint8
    )


__all__ = ["HRVITONBackend", "WEIGHT_FILES"]
