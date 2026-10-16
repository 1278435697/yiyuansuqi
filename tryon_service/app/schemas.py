"""请求/响应数据契约（Pydantic v2）。"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Quality = Literal["fast", "hd"]
TaskStatus = Literal["pending", "running", "succeeded", "failed"]
GarmentCategory = Literal["top", "dress", "skirt", "robe"]


class Keypoint(BaseModel):
    name: str
    x: float
    y: float
    visibility: float = 1.0


class TraceCard(BaseModel):
    """史料溯源卡片，与「衣溯」主题联动。"""

    garment_id: str
    name: str
    dynasty: str
    category: str
    source_text: str = ""
    references: list[str] = Field(default_factory=list)


class GarmentOut(BaseModel):
    id: str
    name: str
    dynasty: str
    category: GarmentCategory
    tags: list[str] = Field(default_factory=list)
    image_url: str
    thumb_url: str
    keypoints: list[Keypoint] = Field(default_factory=list)
    source_text: str = ""
    references: list[str] = Field(default_factory=list)

    @field_validator("tags", "keypoints", "references", mode="before")
    @classmethod
    def _none_to_list(cls, value: Any) -> Any:
        return [] if value is None else value


class TryOnRequest(BaseModel):
    """Base64 入参形式（前端压缩后主用）。"""

    person_image: str = Field(..., description="用户真人照片，Base64（可含 data:image/...;base64, 前缀）")
    garment_id: str | None = Field(default=None, description="素材库服饰 ID，与 garment_image 二选一")
    garment_image: str | None = Field(default=None, description="临时上传的服饰图，Base64")
    quality: Quality = "fast"
    keep_source_pose: bool = Field(
        default=True,
        description="预留字段：当前兜底与 HR-VITON 链路均不改动人体姿态，传 false 也不会重排",
    )
    force_refresh: bool = Field(
        default=False,
        description="跳过磁盘缓存重算一次；同一人像+同一服饰+同一画质默认会直接复用上次结果",
    )

    @model_validator(mode="after")
    def _require_garment(self) -> "TryOnRequest":
        if not self.garment_id and not self.garment_image:
            raise ValueError("garment_id 与 garment_image 必须至少提供一个")
        return self

    @field_validator("person_image")
    @classmethod
    def _not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("person_image 不能为空")
        return value


class TryOnResult(BaseModel):
    task_id: str
    status: TaskStatus
    result_url: str | None = None
    person_mask_url: str | None = None
    pose_overlay_url: str | None = None
    garment_warp_url: str | None = None
    backend_used: str
    warnings: list[str] = Field(default_factory=list)
    timings: dict[str, float] = Field(default_factory=dict)
    trace_card: TraceCard | None = None
    error_code: str | None = None
    message: str | None = None

    @field_validator("warnings", mode="before")
    @classmethod
    def _none_to_list(cls, value: Any) -> Any:
        return [] if value is None else value


class BatchTryOnRequest(BaseModel):
    person_image: str
    garment_ids: list[str] = Field(default_factory=list, min_length=1, max_length=8)
    quality: Quality = "fast"
    force_refresh: bool = Field(default=False, description="同 /tryon 的 force_refresh，作用于每一件")

    @field_validator("garment_ids")
    @classmethod
    def _dedup(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        out = []
        for item in value:
            if item and item not in seen:
                seen.add(item)
                out.append(item)
        if not out:
            raise ValueError("garment_ids 不能为空")
        return out


class TryOnRecordOut(BaseModel):
    id: int
    task_id: str
    garment_id: str | None
    garment_name: str | None
    person_url: str
    result_url: str
    backend_used: str
    quality: str
    warnings: list[str] = Field(default_factory=list)
    created_at: str

    @field_validator("warnings", mode="before")
    @classmethod
    def _none_to_list(cls, value: Any) -> Any:
        return [] if value is None else value


class HistoryPage(BaseModel):
    """试穿记录分页响应。"""

    items: list[TryOnRecordOut] = Field(default_factory=list)
    total: int = 0
    limit: int = 30
    offset: int = 0


class HealthOut(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    vton_backend_configured: str
    vton_backend_resolved: str
    fallback_reason: str | None = None
    gpu_available: bool
    components: dict[str, Any] = Field(default_factory=dict)
    garments_count: int = 0
