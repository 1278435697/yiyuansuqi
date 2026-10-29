"""全局配置。

所有配置项均可通过环境变量（前缀 YISU_）或 backend/.env 覆盖，
代码内提供合理默认值，保证「零配置也能启动」。
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

# backend/（或 tryon_service/）目录，作为所有相对路径的锚点
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
    vton_backend: str = Field(default="auto", description="auto | aidge | hrviton | tps | mock")
    force_cpu: bool = False

    # ---------- 云端试衣：阿里云 Aidge 虚拟试穿 ----------
    # AK/SK 只从环境变量（YISU_AIDGE_ACCESS_KEY_ID / _SECRET）或 systemd EnvironmentFile 注入，
    # 不写进 .env 以外的任何文件；缺任一凭据时后端自检直接判不可用，流水线降级到本地引擎。
    aidge_access_key_id: str = ""
    aidge_access_key_secret: str = ""
    aidge_endpoint: str = "aidge.cn-beijing.aliyuncs.com"
    aidge_resolution: str = Field(default="1K", description="1K | 2K，必填档位；2K 更贵")
    aidge_timeout_seconds: int = Field(default=120, ge=10, le=600)
    # 留空 = 按素材 category 推导（robe/dress→dresses、top→tops、skirt→bottoms）。
    # 实测 Auto 会把汉服大袖袍当成现代上衣，所以默认不交给它判断。
    aidge_cloth_type: str = ""

    # ---------- 出箱（交给云端厂商的一次性图片 URL）----------
    public_base_url: str = Field(
        default="",
        description="厂商能回访到的本服务地址，如 http://47.93.14.11；留空则云端后端不可用",
    )
    outbox_ttl_seconds: int = Field(default=600, ge=30, le=3600)

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

    # ---------- 静态资源 URL 前缀（并入 yisu-ai-platform 后与平台网关对齐）----------
    # 只挂「素材 + 示例图 + 结果图」三类对外资产，不再整体暴露 data/：
    # data/uploads/ 里是用户真人照片的原图，任何情况下都不该被 URL 直读。
    asset_url_prefix: str = Field(default="/tryon-assets", description="素材图/示例图挂载前缀（本服务提供）")
    results_url_prefix: str = Field(
        default="/tryon-results",
        description="结果图 URL 前缀。默认由本服务挂载 results_dir 提供；"
        "若把 results_root 指到平台的 backend/uploads/tryon，就应同时改成 /uploads/tryon，"
        "复用平台 nginx 既有的 /uploads 规则，生产不必新增 location",
    )
    results_root: Path | None = Field(default=None, description="结果图落盘根目录，留空 = <data_dir>/results")

    # ---------- 数据库 ----------
    # 两张试穿表已并入平台主库：本机默认落在平台的 SQLite 正式库上（免装 MySQL 也能跑），
    # 生产用 YISU_DATABASE_URL=mysql+pymysql://… 覆盖。留空时由 platform_db_path 推导。
    platform_db_path: Path = BACKEND_ROOT.parent / "backend" / "data" / "yisu_prod.db"
    database_url: str = Field(default="", description="留空则用 sqlite+aiosqlite:///<platform_db_path>")
    sqlite_wal: bool = Field(
        default=False,
        description="是否把 SQLite 切到 WAL。WAL 会写进库文件（持久），且会多出 -wal/-shm 旁文件；"
        "平台已有按单文件拷贝/导出库的习惯，因此默认不改，靠 busy_timeout 抗瞬时锁冲突；"
        "确实需要读写不互斥时再用 YISU_SQLITE_WAL=true 打开",
    )

    # ---------- CORS ----------
    # 逗号分隔，如 `YISU_CORS_ORIGINS=http://a,http://b`；同源部署（nginx 统一入口）写成空值即可。
    # NoDecode 是必需的：pydantic-settings 对 list 字段会先按 JSON 解，`.env` 里写
    # `YISU_CORS_ORIGINS=`（清空的常见写法）会在 source 层直接抛 SettingsError，
    # 连配置对象都构造不出来，服务起都起不来（云端首次部署实测撞到）。
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # ---------- 缓存 ----------
    enable_disk_cache: bool = True

    # ---------- 结果图 TTL ----------
    results_ttl_days: int = Field(
        default=30,
        ge=1,
        description="结果目录保留天数，超过此期限的 task 目录与对应数据库行将被清理脚本删除",
    )

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

    @field_validator("data_dir", "weights_dir", "logs_dir", "platform_db_path", mode="after")
    @classmethod
    def _abs_path(cls, value: Path) -> Path:
        return value if value.is_absolute() else (BACKEND_ROOT / value).resolve()

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """空串/空白 → 空列表（等于不放通任何跨域源）；`a, b` → 列表；已是列表原样放行。"""
        if value is None:
            return []
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    @field_validator("results_root", mode="before")
    @classmethod
    def _blank_results_root(cls, value: object) -> object:
        # .env 里写 `YISU_RESULTS_ROOT=`（空值）等同于不配，别让 pydantic 把空串当路径
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("results_root", mode="after")
    @classmethod
    def _abs_results_root(cls, value: Path | None) -> Path | None:
        if value is None:
            return None
        return value if value.is_absolute() else (BACKEND_ROOT / value).resolve()

    @model_validator(mode="after")
    def _resolve_database_url(self) -> "Settings":
        """未显式给连接串时，指向平台正式库的 SQLite 文件（绝对路径，不受启动目录影响）。"""
        if not self.database_url:
            self.database_url = f"sqlite+aiosqlite:///{self.platform_db_path.as_posix()}"
        return self

    @field_validator("vton_backend", mode="after")
    @classmethod
    def _normalize_backend(cls, value: str) -> str:
        v = value.strip().lower()
        if v not in {"auto", "aidge", "hrviton", "tps", "mock"}:
            raise ValueError(f"未知的 vton_backend: {value}")
        return v

    @field_validator("aidge_resolution", mode="after")
    @classmethod
    def _normalize_resolution(cls, value: str) -> str:
        v = value.strip().upper()
        if v not in {"1K", "2K"}:
            raise ValueError(f"未知的 aidge_resolution: {value}（只支持 1K / 2K）")
        return v

    # ---------- 派生目录 ----------
    @property
    def garments_dir(self) -> Path:
        return self.data_dir / "garments"

    @property
    def outbox_dir(self) -> Path:
        """交给云端厂商的临时出件目录：短 TTL、调用结束即删，不属于任何静态挂载。"""
        return self.data_dir / "outbox"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def samples_dir(self) -> Path:
        return self.data_dir / "samples"

    @property
    def results_dir(self) -> Path:
        return self.results_root if self.results_root is not None else self.data_dir / "results"

    @property
    def person_sources_dir(self) -> Path:
        """用户原图落盘目录，不在静态挂载下，只能通过 API 端点访问。"""
        return self.data_dir / "private" / "person_sources"

    @property
    def results_served_externally(self) -> bool:
        """结果目录被挪到 data/ 之外（如平台 backend/uploads/tryon）时为 True。

        此时本服务的静态挂载覆盖不到它，URL 前缀必须由宿主（平台 nginx / vite 代理）提供，
        main.py 据此决定要不要挂 results_url_prefix。
        """
        try:
            self.results_dir.resolve().relative_to(self.data_dir.resolve())
        except ValueError:
            return True
        return False

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
            self.samples_dir,
            self.uploads_dir,
            self.results_dir,
            self.cache_dir,
            self.outbox_dir,
            self.person_sources_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
