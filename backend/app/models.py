from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
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
    shop_name: Mapped[str | None] = mapped_column(String(200))
    seller_rating: Mapped[float | None] = mapped_column(Float)
    commission_amount: Mapped[float | None] = mapped_column(Float)  # số tiền do API cung cấp (nếu có)
    country: Mapped[str | None] = mapped_column(String(2))
    created_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)

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


class User(Base):
    """Ứng dụng chạy local một người dùng; bảng này sẵn sàng cho nhiều người dùng sau này."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MarketplaceConnection(Base):
    """Chỉ lưu token do cơ chế ủy quyền chính thức cấp. KHÔNG BAO GIỜ lưu username/password."""
    __tablename__ = "marketplace_connections"
    __table_args__ = (UniqueConstraint("user_id", "marketplace", name="uq_user_marketplace"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    marketplace: Mapped[str] = mapped_column(String(20))
    connection_status: Mapped[str] = mapped_column(String(20), default="not_linked")
    access_token_encrypted: Mapped[str | None] = mapped_column(Text)
    refresh_token_encrypted: Mapped[str | None] = mapped_column(Text)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime)
    scopes: Mapped[str | None] = mapped_column(Text)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow)


class ProductSnapshot(Base):
    __tablename__ = "product_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    price: Mapped[float | None] = mapped_column(Float)
    commission_rate: Mapped[float | None] = mapped_column(Float)
    rating: Mapped[float | None] = mapped_column(Float)
    review_count: Mapped[int | None] = mapped_column(Integer)
    sales_count: Mapped[int | None] = mapped_column(Integer)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AffiliateLink(Base):
    __tablename__ = "affiliate_links"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(1000))
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual | api
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ProductScore(Base):
    __tablename__ = "product_scores"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    score: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    breakdown: Mapped[dict | None] = mapped_column(JSON)
    formula_version: Mapped[str] = mapped_column(String(20), default="v1")
    computed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending|running|paused|done|failed
    params: Mapped[dict | None] = mapped_column(JSON)
    max_products: Mapped[int] = mapped_column(Integer, default=50)
    products_found: Mapped[int] = mapped_column(Integer, default=0)
    requests_made: Mapped[int] = mapped_column(Integer, default=0)
    resume_cursor: Mapped[dict | None] = mapped_column(JSON)  # để tiếp tục scan bị gián đoạn
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime)


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_job_id: Mapped[int] = mapped_column(ForeignKey("scan_jobs.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"))
    external_id: Mapped[str | None] = mapped_column(String(120))
    outcome: Mapped[str] = mapped_column(String(20))  # new | duplicate | error
    message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AIAnalysis(Base):
    __tablename__ = "ai_analysis"

    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(30))
    model: Mapped[str | None] = mapped_column(String(80))
    kind: Mapped[str] = mapped_column(String(30), default="product")  # product | review
    result: Mapped[dict | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="ok")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class ApiUsageLog(Base):
    __tablename__ = "api_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    service: Mapped[str] = mapped_column(String(30), index=True)  # shopee | tiktok_shop | ollama
    endpoint: Mapped[str | None] = mapped_column(String(200))
    status_code: Mapped[int | None] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    error_code: Mapped[str | None] = mapped_column(String(60))
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
