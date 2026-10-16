"""薄板样条（Thin-Plate Spline）变换求解。

用于兜底试穿：把服饰图的控制点（领口/肩线/腰/袖口/衣摆）形变映射到人体关键点。
采用带仿射项的 TPS，避免纯样条在点稀疏时的过度扭曲。
参考 Book(1989) 与 city93/thin_plate_spline 的实现思路，纯 numpy/scipy，不依赖 OpenCV。
"""

from __future__ import annotations

import numpy as np


def _kernel_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """phi(r) = r^2 * log(r^2)，a:(n,2)、b:(m,2) → (n,m)。"""
    diff = a[:, None, :] - b[None, :, :]
    dist_sq = np.clip(np.einsum("nmd,nmd->nm", diff, diff), 1e-12, None)
    return dist_sq * np.log(dist_sq)


class ThinPlateSpline:
    """拟合 src→dst 控制点对，得到可对任意坐标求值的形变场。"""

    def __init__(self, lam: float = 1e-3) -> None:
        self.lam = lam
        self._src: np.ndarray | None = None
        self._weights: np.ndarray | None = None
        self._affine: np.ndarray | None = None

    @property
    def fitted(self) -> bool:
        return self._weights is not None

    def fit(self, src: np.ndarray, dst: np.ndarray) -> "ThinPlateSpline":
        src = np.asarray(src, dtype=np.float64)
        dst = np.asarray(dst, dtype=np.float64)
        if src.ndim != 2 or src.shape != dst.shape or src.shape[1] != 2:
            raise ValueError(f"控制点形状不匹配: src{src.shape} dst{dst.shape}")
        n = src.shape[0]
        if n < 3:
            raise ValueError("TPS 至少需要 3 对控制点")

        k = _kernel_matrix(src, src)
        p = np.hstack([np.ones((n, 1)), src])  # (n,3)
        system = np.block(
            [
                [k + self.lam * np.eye(n), p],
                [p.T, np.zeros((3, 3))],
            ]
        )
        rhs = np.vstack([dst, np.zeros((3, dst.shape[1]))])  # (n+3, 2)
        try:
            solution = np.linalg.solve(system, rhs)
        except np.linalg.LinAlgError:
            solution = np.linalg.lstsq(system, rhs, rcond=None)[0]

        self._src = src
        self._weights = solution[:n]
        self._affine = solution[n:]
        return self

    def transform(self, points: np.ndarray) -> np.ndarray:
        """points:(m,2) 源坐标 → 目标坐标 (m,2)。"""
        if not self.fitted or self._src is None:
            raise RuntimeError("ThinPlateSpline 尚未 fit")
        pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
        basis = np.hstack([np.ones((pts.shape[0], 1)), pts])  # (m,3)
        kernel = _kernel_matrix(pts, self._src)  # (m,n)
        return basis @ self._affine + kernel @ self._weights


def warp_image_forward(
    image: np.ndarray,
    mask: np.ndarray,
    src_points: np.ndarray,
    dst_points: np.ndarray,
    out_shape: tuple[int, int],
    *,
    lam: float = 1e-3,
    order: int = 1,
    pad: int = 24,
) -> tuple[np.ndarray, np.ndarray, tuple[int, int, int, int]]:
    """把 image 按 src→dst 控制点对形变到 out_shape 坐标系。

    只在目标包围盒（含 pad 边距）内计算，降低内存与耗时。
    返回 (warp_rgb, warp_mask, (y0, y1, x0, x1))，坐标为 out_shape 全图坐标系下的窗口。
    """
    from scipy.ndimage import map_coordinates

    h_out, w_out = out_shape[:2]
    dst = np.asarray(dst_points, dtype=np.float64)
    x0 = max(0, int(np.floor(dst[:, 0].min())) - pad)
    x1 = min(w_out, int(np.ceil(dst[:, 0].max())) + pad)
    y0 = max(0, int(np.floor(dst[:, 1].min())) - pad)
    y1 = min(h_out, int(np.ceil(dst[:, 1].max())) + pad)
    if x1 - x0 < 4 or y1 - y0 < 4:
        raise ValueError("目标控制点包围盒过小，无法形变")

    # 反向拟合 dst→src，得到目标网格每个像素对应的源坐标
    inverse = ThinPlateSpline(lam=lam).fit(dst, np.asarray(src_points, dtype=np.float64))
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
    grid = np.column_stack([xx.ravel(), yy.ravel()])
    sample = inverse.transform(grid).reshape(yy.shape[0], yy.shape[1], 2)
    src_x, src_y = sample[..., 0], sample[..., 1]

    channels = image.shape[2] if image.ndim == 3 else 1
    arr = image if image.ndim == 3 else image[..., None]
    warped = np.empty((yy.shape[0], yy.shape[1], channels), dtype=np.float32)
    for c in range(channels):
        warped[..., c] = map_coordinates(
            arr[..., c].astype(np.float32), [src_y, src_x], order=order, mode="nearest"
        )

    inside_bbox = (src_x >= 0) & (src_x <= arr.shape[1] - 1) & (src_y >= 0) & (src_y <= arr.shape[0] - 1)
    sampled_mask = map_coordinates(
        mask.astype(np.float32), [src_y, src_x], order=order, mode="constant", cval=0.0
    )
    warp_mask = np.clip(sampled_mask * inside_bbox, 0, 255).astype(np.uint8)
    return np.clip(warped, 0, 255).astype(np.uint8), warp_mask, (y0, y1, x0, x1)


__all__ = ["ThinPlateSpline", "warp_image_forward"]
