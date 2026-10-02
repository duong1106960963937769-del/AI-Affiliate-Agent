from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("platform", "external_id", name="uq_platform_external"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), index=True)  # shopee | tiktok_shop
    external_id: Mapped[str] = mapped_column(String(120))
    name: Mapped[str] = mapped_column(String(300), index=True)
    url: Mapped[str | None] = mapped_column(String(1000))
    image_url: Mapped[str | None] = mapped_column(String(1000))
    category: Mapped[str | None] = mapped_column(String(120), index=True)
    price: Mapped[float | None] = mapped_column(Float)
    currency: Mapped[str] = mapped_column(String(3), default="VND")
    commission_rate: Mapped[float | None] = mapped_column(Float)  # % danh nghĩa
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    positive_review_pct: Mapped[float | None] = mapped_column(Float)
    negative_review_pct: Mapped[float | None] = mapped_column(Float)
    sold_count: Mapped[int | None] = mapped_column(Integer)  # tổng đã bán
    sold_30d: Mapped[int | None] = mapped_column(Integer)
    sold_prev_30d: Mapped[int | None] = mapped_column(Integer)
    competition: Mapped[str | None] = mapped_column(String(10))  # low | medium | high
    return_rate: Mapped[float | None] = mapped_column(Float)  # % hoàn/hủy
    video_fit: Mapped[float | None] = mapped_column(Float)  # 0-5, do người dùng đánh giá
    data_updated_at: Mapped[datetime | None] = mapped_column(DateTime)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    source: Mapped[str] = mapped_column(String(10), default="csv", index=True)  # demo | csv | manual
    source_label: Mapped[str | None] = mapped_column(String(200))
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False)

    @property
    def is_demo(self) -> bool:
        return self.source == "demo"


class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ImportLog(Base):
    __tablename__ = "import_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(300))
    created: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    rejected: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
