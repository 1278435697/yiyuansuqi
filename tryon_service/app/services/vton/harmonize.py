"""光影匹配（色彩迁移）。

把服饰图的整体亮度/色度增益向人体躯干区域统计量对齐，
采用 Reinhard 的 LAB 均值-方差迁移，纯 numpy 实现。
"""

from __future__ import annotations

import numpy as np

_SRGB_TO_LINEAR = 1 / 2.4


def _rgb_to_linear(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(np.float32) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _linear_to_rgb(linear: np.ndarray) -> np.ndarray:
    c = np.clip(linear, 0.0, 1.0)
    c = np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)
    return np.clip(c * 255.0, 0, 255).astype(np.uint8)


def rgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """sRGB uint8 → Lab float32（D65）。"""
    linear = _rgb_to_linear(rgb)
    m = np.array(
        [[0.4124564, 0.3575761, 0.1804375],
         [0.2126729, 0.7151522, 0.0721750],
         [0.0193339, 0.1191920, 0.9503041]],
        dtype=np.float32,
    )
    xyz = linear @ m.T
    ref = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    f = xyz / ref
    delta = np.float32(6 / 29)
    f = np.where(f > delta**3, np.cbrt(f), f / (3 * delta**2) + 4 / 29)
    lab = np.empty_like(f)
    lab[..., 0] = 116 * f[..., 1] - 16
    lab[..., 1] = 500 * (f[..., 0] - f[..., 1])
    lab[..., 2] = 200 * (f[..., 1] - f[..., 2])
    return lab


def lab_to_rgb(lab: np.ndarray) -> np.ndarray:
    """Lab float32 → sRGB uint8。"""
    y = (lab[..., 0] + 16) / 116
    x = lab[..., 1] / 500 + y
    z = y - lab[..., 2] / 200
    delta = np.float32(6 / 29)

    def finv(t: np.ndarray) -> np.ndarray:
        return np.where(t > delta, t**3, 3 * delta**2 * (t - 4 / 29))

    ref = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
    xyz = np.stack([finv(x), finv(y), finv(z)], axis=-1) * ref
    m_inv = np.array(
        [[3.2404542, -1.5371385, -0.4985314],
         [-0.9692660, 1.8760108, 0.0415560],
         [0.0556434, -0.2040259, 1.0572252]],
        dtype=np.float32,
    )
    return _linear_to_rgb(xyz @ m_inv.T)


def transfer_lab(source: np.ndarray, target_stats: np.ndarray, strength: float = 0.6) -> np.ndarray:
    """把 source(RGB uint8) 的 Lab 统计量向 target_stats 对齐。

    target_stats: shape (N,3) 的目标区域 Lab 样本。strength=0 时完全不变。
    仅调整均值，方差按比例适度收缩，避免丢掉布料本身的层次。
    """
    if target_stats.size == 0 or strength <= 0:
        return source
    src_lab = rgb_to_lab(source).reshape(-1, 3)
    tgt = target_stats.reshape(-1, 3).astype(np.float32)
    src_mean, src_std = src_lab.mean(axis=0), src_lab.std(axis=0) + 1e-6
    tgt_mean, tgt_std = tgt.mean(axis=0), tgt.std(axis=0) + 1e-6

    ratio = np.clip(tgt_std / src_std, 0.75, 1.35)  # 限制缩放幅度，防止过曝/死黑
    shifted = (src_lab - src_mean) * (1 + strength * (ratio - 1)) + src_mean
    adjusted = shifted + strength * (tgt_mean - src_mean)
    out = adjusted.reshape(source.shape[:2] + (3,))
    return lab_to_rgb(np.clip(out, [-100, -130, -130], [100, 120, 120]))


def sample_lab(image: np.ndarray, mask: np.ndarray, max_samples: int = 20000) -> np.ndarray:
    """按掩码从图中抽样 Lab 统计样本。"""
    binary = mask > 127
    if not binary.any():
        return np.empty((0, 3), dtype=np.float32)
    pixels = image[binary].astype(np.float32)[None, :, :]
    lab = rgb_to_lab(pixels)[0]
    if lab.shape[0] > max_samples:
        idx = np.random.default_rng(0).choice(lab.shape[0], max_samples, replace=False)
        lab = lab[idx]
    return lab
