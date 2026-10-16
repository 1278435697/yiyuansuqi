"""人像分割 Provider 抽象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np


@dataclass
class SegmentResult:
    """分割输出。

    person:  人体前景掩码 (H,W) uint8, 0/255
    clothes: 服饰语义区域 (H,W) uint8, 0/255；仅语义解析 Provider 能提供，
             缺失时为 None，TPS 合成会用 person 掩码的躯干近似代替。
    """

    person: np.ndarray
    clothes: np.ndarray | None = None
    provider: str = "unknown"
    notes: list[str] = field(default_factory=list)
    # 额外语义区域（仅语义解析 Provider 会给出），常见 key：arms / hands / head / legs
    extra: dict[str, np.ndarray] = field(default_factory=dict)


class SegmentProvider(Protocol):
    name: str

    def available(self) -> tuple[bool, str | None]:
        """返回 (是否可用, 不可用原因)。探测必须轻量，不做真实推理。"""

    def segment(self, rgb: np.ndarray) -> SegmentResult:
        """输入 RGB uint8 (H,W,3)，输出掩码。失败需抛异常，由上层降级处理。"""
