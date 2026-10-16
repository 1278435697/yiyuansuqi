"""试穿推理后端抽象与上下文。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np

from app.services.garments import GarmentAsset
from app.services.pose.base import PoseResult


@dataclass
class TryOnContext:
    """一次试穿请求的全部输入。"""

    person_rgb: np.ndarray
    person_mask: np.ndarray
    pose: PoseResult
    garment: GarmentAsset
    quality: str = "fast"
    out_dir: Path | None = None
    clothes_mask: np.ndarray | None = None
    arms_mask: np.ndarray | None = None
    head_mask: np.ndarray | None = None
    extra: dict[str, np.ndarray] = field(default_factory=dict)

    @property
    def shape(self) -> tuple[int, int]:
        return self.person_rgb.shape[:2]


@dataclass
class TryOnOutput:
    """后端输出：合成结果 + 供展示/后处理的中间图。"""

    result: np.ndarray
    warped_rgb: np.ndarray | None = None
    warped_mask: np.ndarray | None = None
    warp_window: tuple[int, int, int, int] | None = None
    backend: str = "unknown"
    notes: list[str] = field(default_factory=list)


class VTONBackendProtocol(Protocol):
    name: str

    def available(self) -> tuple[bool, str | None]: ...

    def run(self, ctx: TryOnContext) -> TryOnOutput: ...


def body_anchor_points(pose: PoseResult) -> dict[str, tuple[float, float]]:
    """TPS 目标锚点：由人体姿态给出的身体部位像素坐标。"""
    cx = pose.shoulder_center[0]
    anchors: dict[str, tuple[float, float]] = {
        "shoulder_L": (
            pose.keypoints["L_shoulder"].xy()
            if pose.get("L_shoulder")
            else (cx - pose.shoulder_width / 2, pose.shoulder_center[1])
        ),
        "shoulder_R": (
            pose.keypoints["R_shoulder"].xy()
            if pose.get("R_shoulder")
            else (cx + pose.shoulder_width / 2, pose.shoulder_center[1])
        ),
    }
    sh_y = pose.shoulder_center[1]
    hip_y = pose.hip_center[1]
    torso = max(1.0, hip_y - sh_y)
    # 领口位于肩线上方约 0.18 个躯干长
    anchors["collar_center"] = (cx, sh_y - torso * 0.18)
    waist_y = sh_y + torso * 0.72
    half_waist = max(4.0, pose.hip_width * 0.52)
    anchors["waist_L"] = (cx - half_waist, waist_y)
    anchors["waist_R"] = (cx + half_waist, waist_y)
    # 袖口：肩点外下方，按肘/腕可见性取更可信的一个
    for side in ("L", "R"):
        shoulder = anchors[f"shoulder_{side}"]
        elbow, wrist = pose.get(f"{side}_elbow"), pose.get(f"{side}_wrist")
        if elbow and elbow.visibility >= 0.5:
            anchors[f"sleeve_{side}_end"] = (elbow.x, max(elbow.y, shoulder[1] + torso * 0.1))
        elif wrist and wrist.visibility >= 0.5:
            anchors[f"sleeve_{side}_end"] = (wrist.x, max(wrist.y, shoulder[1] + torso * 0.15))
        else:
            anchors[f"sleeve_{side}_end"] = (
                shoulder[0] + (shoulder[0] - cx) * 0.35,
                shoulder[1] + torso * 0.55,
            )
    hem_y = max(pose.hem_y, waist_y + torso * 0.35)
    half_hem = max(6.0, pose.hip_width * 0.75)
    anchors["hem_L"] = (cx - half_hem, hem_y)
    anchors["hem_R"] = (cx + half_hem, hem_y)
    return anchors


__all__ = ["TryOnContext", "TryOnOutput", "VTONBackendProtocol", "body_anchor_points"]
