"""全局配置。

所有配置项均可通过环境变量（前缀 YISU_）或 backend/.env 覆盖，
代码内提供合理默认值，保证「零配置也能启动」。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ 目录，作为所有相对路径的锚点
BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_ROOT / ".env",
        env_file_encoding="utf-8",
        env_prefix="YISU_",
        extra="ignore",
    )

    app_name: str = "衣溯AI · 虚拟试穿服务"
    api_prefix: str = "/api/v1"

    # ---------- 路径 ----------
    data_dir: Path = BACKEND_ROOT / "data"
    weights_dir: Path = BACKEND_ROOT / "weights"
    logs_dir: Path = BACKEND_ROOT / "logs"

    # ---------- 推理后端 ----------
    vton_backend: str = Field(default="auto", description="auto | hrviton | tps | mock")
    force_cpu: bool = False

    # ---------- 可选权重（均为具体文件/目录路径，缺省仅做约定，不存在则自动降级）----------
    vitongpu_onnx: Path | None = Field(default=None, description="gcpait_vitongpu_2k.onnx 路径")
    u2net_onnx: Path | None = Field(default=None, description="u2net.onnx 路径")
    hrviton_ckpt_dir: Path | None = Field(default=None, description="HR-VITON .pth 所在目录")
    # HR-VITON 推理命令模板，可用占位符：{person} {garment} {out_dir} {repo} {weights} {resolution}
    hrviton_command: str = (
        "python inference.py --inputs {person} --clothes {garment} "
        "--outputs {out_dir} --cuda --model_dir {weights} --resolution {resolution}"
    )

    # ---------- 上传与输出 ----------
    max_upload_mb: float = Field(default=12.0, gt=0, le=64)
    output_long_side: int = Field(default=1024, ge=256, le=2048)

    # ---------- 数据库 ----------
    database_url: str = "sqlite+aiosqlite:///./data/yisu.db"

    # ---------- CORS ----------
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ---------- 缓存 ----------
    enable_disk_cache: bool = True

    @field_validator("vitongpu_onnx", "u2net_onnx", mode="after")
    @classmethod
    def _default_weight_path(cls, value: Path | None, info) -> Path:
        if value is not None:
            return value if value.is_absolute() else (BACKEND_ROOT / value).resolve()
        # 缺省按官方文件名约定到 weights/ 下（不存在时 Provider 自检会返回不可用）
        filename = "gcpait_vitongpu_2k.onnx" if info.field_name == "vitongpu_onnx" else "u2net.onnx"
        return BACKEND_ROOT / "weights" / filename

    @field_validator("hrviton_ckpt_dir", mode="after")
    @classmethod
    def _default_hrviton_dir(cls, value: Path | None) -> Path:
        if value is not None:
            return value if value.is_absolute() else (BACKEND_ROOT / value).resolve()
        return BACKEND_ROOT / "weights" / "hrviton"

    @field_validator("data_dir", "weights_dir", "logs_dir", mode="after")
    @classmethod
    def _abs_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else (BACKEND_ROOT / value).resolve()

    @field_validator("vton_backend", mode="after")
    @classmethod
    def _normalize_backend(cls, value: str) -> str:
        v = value.strip().lower()
        if v not in {"auto", "hrviton", "tps", "mock"}:
            raise ValueError(f"未知的 vton_backend: {value}")
        return v

    # ---------- 派生目录 ----------
    @property
    def garments_dir(self) -> Path:
        return self.data_dir / "garments"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"

    @property
    def cache_dir(self) -> Path:
        return self.data_dir / "cache"

    @property
    def garments_index(self) -> Path:
        return self.garments_dir / "index.json"

    def ensure_dirs(self) -> None:
        for path in (
            self.data_dir,
            self.weights_dir,
            self.logs_dir,
            self.garments_dir,
            self.uploads_dir,
            self.results_dir,
            self.cache_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
