"""人体姿态与关键点抽象。

统一输出 COCO-17 关键点：
nose, L_eye, R_eye, L_ear, R_ear, L_shoulder, R_shoulder,
L_elbow, R_elbow, L_wrist, R_wrist, L_hip, R_hip, L_knee, R_knee, L_ankle, R_ankle
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

COCO_KEYPOINT_17: tuple[str, ...] = (
    "nose",
    "L_eye",
    "R_eye",
    "L_ear",
    "R_ear",
    "L_shoulder",
    "R_shoulder",
    "L_elbow",
    "R_elbow",
    "L_wrist",
    "R_wrist",
    "L_hip",
    "R_hip",
    "L_knee",
    "R_knee",
    "L_ankle",
    "R_ankle",
)

# BlazePose 33 点 → COCO-17 的索引映射
BLAZEPOSE_TO_COCO17: tuple[int, ...] = (
    0,  # nose
    2,  # L_eye
    5,  # R_eye
    7,  # L_ear
    8,  # R_ear
    11,  # L_shoulder
    12,  # R_shoulder
    13,  # L_elbow
    14,  # R_elbow
    15,  # L_wrist
    16,  # R_wrist
    23,  # L_hip
    24,  # R_hip
    25,  # L_knee
    26,  # R_knee
    27,  # L_ankle
    28,  # R_ankle
)


@dataclass
class Keypoint:
    name: str
    x: float  # 像素坐标
    y: float
    visibility: float = 1.0

    def xy(self) -> tuple[float, float]:
        return self.x, self.y


@dataclass
class PoseResult:
    """姿态结果，供 TPS 构造目标锚点。"""

    keypoints: dict[str, Keypoint]
    provider: str = "unknown"
    notes: list[str] = field(default_factory=list)
    # 由关键点或掩码推导出的身体几何量（像素）
    shoulder_center: tuple[float, float] = (0.0, 0.0)
    shoulder_width: float = 1.0
    shoulder_angle: float = 0.0  # 相对水平轴的倾角（弧度）
    hip_center: tuple[float, float] = (0.0, 0.0)
    hip_width: float = 1.0
    waist_y: float = 0.0
    hem_y: float = 0.0  # 建议的衣摆下沿（膝盖附近）

    @property
    def torso_length(self) -> float:
        return max(1.0, abs(self.hip_center[1] - self.shoulder_center[1]))

    def get(self, name: str) -> Keypoint | None:
        return self.keypoints.get(name)

    def to_output(self) -> list[dict[str, float | str]]:
        return [
            {
                "name": kp.name,
                "x": round(kp.x, 2),
                "y": round(kp.y, 2),
                "visibility": round(kp.visibility, 3),
            }
            for kp in self.keypoints.values()
        ]

    def refresh_geometry(self) -> None:
        """由关键点计算肩线/腰线/衣摆等身体几何量，TPS 依赖这些量构造目标锚点。"""
        ls, rs = self.get("L_shoulder"), self.get("R_shoulder")
        lh, rh = self.get("L_hip"), self.get("R_hip")
        if ls and rs:
            self.shoulder_center = _midpoint(ls, rs)
            self.shoulder_width = max(1.0, abs(ls.x - rs.x))
            self.shoulder_angle = estimate_angle(ls, rs)
        if lh and rh:
            self.hip_center = _midpoint(lh, rh)
            self.hip_width = max(1.0, abs(lh.x - rh.x))
            self.waist_y = self.hip_center[1]
        elif ls and rs:
            # 腰部不可见（长裙/截断）时，按肩宽推算腰线位置
            self.hip_center = (self.shoulder_center[0], self.shoulder_center[1] + self.shoulder_width * 1.35)
            self.hip_width = self.shoulder_width * 0.85
            self.waist_y = self.hip_center[1]
        # 掩码几何估计可能把肩线与腰线落在同一行，躯干长度趋 0 会让 TPS 锚点退化成一条线
        min_torso = max(12.0, self.shoulder_width * 0.75)
        if self.hip_center[1] <= self.shoulder_center[1] + min_torso * 0.3:
            self.hip_center = (self.hip_center[0], self.shoulder_center[1] + min_torso)
            self.waist_y = self.hip_center[1]
        knee = self.get("L_knee")
        if knee and knee.y > self.waist_y + min_torso * 0.3:
            self.hem_y = knee.y
        elif ls and rs:
            self.hem_y = self.shoulder_center[1] + self.shoulder_width * 2.6
        else:
            self.hem_y = self.waist_y
        self.hem_y = max(self.hem_y, self.waist_y + min_torso * 0.6)


def build_pose_from_points(
    points: dict[str, tuple[float, float, float]], provider: str, notes: list[str] | None = None
) -> PoseResult:
    """由 {name: (x, y, visibility)} 构造 PoseResult 并计算身体几何量。"""
    keypoints = {
        name: Keypoint(name=name, x=float(p[0]), y=float(p[1]), visibility=float(p[2]))
        for name, p in points.items()
    }
    result = PoseResult(
        keypoints=keypoints, provider=provider, notes=notes or [],
    )
    result.refresh_geometry()
    return result


def _midpoint(a: Keypoint, b: Keypoint) -> tuple[float, float]:
    return (a.x + b.x) / 2.0, (a.y + b.y) / 2.0


def pose_from_mask(mask: np.ndarray) -> dict[str, tuple[float, float, float]]:
    """无姿态模型时，由人形掩码的宽度分布推断肩线/腰线等锚点（近似 17 点）。"""
    h, w = mask.shape[:2]
    binary = mask > 127
    rows = np.where(binary.any(axis=1))[0]
    if rows.size == 0:
        return {}
    top, bottom = int(rows[0]), int(rows[-1])
    span = max(1, bottom - top)

    widths = binary.sum(axis=1).astype(np.float32)

    def row_width(y: int) -> float:
        y = int(np.clip(y, top, bottom))
        return float(widths[y])

    # 肩线：先找颈部（头部下方最窄处），再向下找宽度明显大于肩颈分界的第一行。
    # 直接取上半身最宽行会命中手臂/臀部，导致肩线过低、躯干长度被压缩为 0。
    head_end = top + int(span * 0.16)
    head_width = max(row_width(y) for y in range(top, min(head_end + 1, bottom + 1)))
    neck_zone = range(top + int(span * 0.10), top + int(span * 0.26) + 1)
    neck_y = min(neck_zone, key=row_width) if neck_zone else head_end
    shoulder_threshold = max(head_width * 1.12, (row_width(neck_y) * 1.8) if neck_y >= top else 0.0, 1.0)
    search_to = min(bottom, neck_y + int(span * 0.32))
    shoulder_y = next(
        (y for y in range(neck_y, search_to + 1) if widths[y] >= shoulder_threshold),
        min(bottom, neck_y + max(4, int(span * 0.06))),
    )
    # 腰线：肩线下方一定距离内的最窄处（正身照通常为腰）
    waist_from = min(bottom, shoulder_y + max(8, int(span * 0.14)))
    waist_to = min(bottom, shoulder_y + int(span * 0.60))
    if waist_to > waist_from:
        waist_y = int(waist_from + np.argmin(widths[waist_from:waist_to]))
    else:
        waist_y = min(bottom, shoulder_y + max(12, int(span * 0.30)))
    waist_y = max(waist_y, shoulder_y + max(10, int(span * 0.12)))

    def half_width(y: int) -> float:
        row = np.where(binary[min(max(y, 0), h - 1)])[0]
        return float(row[-1] - row[0]) if row.size > 1 else float(w * 0.25)

    xs = np.where(binary[min(max(shoulder_y, 0), h - 1)])[0]
    center_x = float(xs.mean()) if xs.size else w / 2.0
    sw = half_width(shoulder_y)
    hw = half_width(waist_y) * 0.95

    torso = max(10.0, float(waist_y - shoulder_y))
    knee_y = min(bottom, int(waist_y + torso * 1.35))
    ankle_y = min(bottom, int(knee_y + torso * 0.85))

    def pair(name_l: str, name_r: str, y: float, width: float) -> dict[str, tuple[float, float, float]]:
        return {
            name_l: (center_x - width / 2.0, y, 0.4),
            name_r: (center_x + width / 2.0, y, 0.4),
        }

    points: dict[str, tuple[float, float, float]] = {
        "nose": (center_x, max(0.0, shoulder_y - span * 0.14), 0.5),
        **pair("L_shoulder", "R_shoulder", shoulder_y, sw),
        **pair("L_hip", "R_hip", waist_y, hw),
        **pair("L_elbow", "R_elbow", shoulder_y + span * 0.18, sw * 1.05),
        **pair("L_wrist", "R_wrist", waist_y + span * 0.06, sw * 1.1),
        **pair("L_knee", "R_knee", knee_y, hw * 0.9),
        **pair("L_ankle", "R_ankle", ankle_y, hw * 0.8),
    }
    return points


def estimate_angle(a: Keypoint, b: Keypoint) -> float:
    return math.atan2(b.y - a.y, b.x - a.x)
