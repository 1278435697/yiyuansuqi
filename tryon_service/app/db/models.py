"""ORM 模型：Garment（服饰素材）与 TryOnRecord（试穿记录）。"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Garment(Base):
    __tablename__ = "garment"
    __table_args__ = (UniqueConstraint("id", name="uq_garment_id"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    dynasty: Mapped[str] = mapped_column(String(32), default="未知")
    category: Mapped[str] = mapped_column(String(16), default="top")
    tags: Mapped[list] = mapped_column(JSON, default=list)
    image_path: Mapped[str] = mapped_column(String(256), nullable=False)
    mask_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    thumb_path: Mapped[str | None] = mapped_column(String(256), nullable=True)
    # 9 个归一化关键点：[{name,x,y}, ...]
    keypoints: Mapped[list] = mapped_column(JSON, default=list)
    bbox_area_ratio: Mapped[float] = mapped_column(Float, default=0.0)
    source_text: Mapped[str] = mapped_column(Text, default="")
    references: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    records: Mapped[list["TryOnRecord"]] = relationship(back_populates="garment")


class TryOnRecord(Base):
    __tablename__ = "tryon_record"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    garment_id: Mapped[str | None] = mapped_column(
        ForeignKey("garment.id", ondelete="SET NULL"), nullable=True
    )
    person_url: Mapped[str] = mapped_column(String(256), default="")
    result_url: Mapped[str] = mapped_column(String(256), default="")
    mask_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    pose_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    warp_url: Mapped[str | None] = mapped_column(String(256), nullable=True)
    backend_used: Mapped[str] = mapped_column(String(32), default="tps")
    quality: Mapped[str] = mapped_column(String(8), default="fast")
    status: Mapped[str] = mapped_column(String(16), default="succeeded")
    warnings: Mapped[list] = mapped_column(JSON, default=list)
    timings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, index=True
    )

    garment: Mapped[Garment | None] = relationship(back_populates="records", lazy="selectin")
