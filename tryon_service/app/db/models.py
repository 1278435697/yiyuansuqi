"""ORM 模型：Garment（服饰素材）与 TryOnRecord（试穿记录）。

两张表已并入平台主库，表名用 `tryon_` 前缀 + 复数，避开平台的 `costumes`/`collections` 等表。
列定义的唯一事实源是 `database/tryon_schema.sql`，两侧（本服务 ORM / 平台 ORM / DDL）一致性由
`tests/test_db_contract.py` 守住，两侧漂移会直接测失败。
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Garment(Base):
    # id 本身就是主键，不再叠 UniqueConstraint（与 database/tryon_schema.sql 保持一致）
    __tablename__ = "tryon_garments"

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
    # 逻辑外键 → 平台 costumes.id：用来把试穿素材与馆藏档案对起来（不建 FK 约束，理由见 TryOnRecord.user_id）
    costume_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    records: Mapped[list["TryOnRecord"]] = relationship(back_populates="garment")


class TryOnRecord(Base):
    __tablename__ = "tryon_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    task_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    garment_id: Mapped[str | None] = mapped_column(
        ForeignKey("tryon_garments.id", ondelete="SET NULL"), nullable=True
    )
    # 逻辑外键（不建 FK 约束）：本服务与平台主库同表不同 ORM 定义，
    # 而测试用的临时库里并没有 users/costumes 表，硬约束会让建表/写入无缘无故地挂。
    # 真正的 FK 声明在 database/tryon_schema.sql（MySQL 生产库）里。
    user_id: Mapped[int | None] = mapped_column(Integer, index=True, nullable=True)
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
