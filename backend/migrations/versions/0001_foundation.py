"""Nền tảng: bảng Phase 1 cũ (nếu chưa có) + bảng mới + cột mới của products

Database tạo từ bản cũ bằng create_all vẫn nâng cấp được: mỗi bước kiểm tra tồn tại trước.

Revision ID: 0001
Revises:
"""
import sqlalchemy as sa
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

NOW = sa.text("CURRENT_TIMESTAMP")


def _pk():
    return sa.Column("id", sa.Integer(), primary_key=True)


def _ts(name="created_at", nullable=False):
    return sa.Column(name, sa.DateTime(), nullable=nullable)


def upgrade() -> None:
    insp = sa.inspect(op.get_bind())
    existing = set(insp.get_table_names())

    if "products" not in existing:
        op.create_table(
            "products", _pk(),
            sa.Column("platform", sa.String(20), nullable=False), sa.Column("external_id", sa.String(120), nullable=False),
            sa.Column("name", sa.String(300), nullable=False), sa.Column("url", sa.String(1000)),
            sa.Column("image_url", sa.String(1000)), sa.Column("category", sa.String(120)),
            sa.Column("price", sa.Float()), sa.Column("currency", sa.String(3), nullable=False, server_default="VND"),
            sa.Column("commission_rate", sa.Float()), sa.Column("rating", sa.Float()),
            sa.Column("review_count", sa.Integer()), sa.Column("positive_review_pct", sa.Float()),
            sa.Column("negative_review_pct", sa.Float()), sa.Column("sold_count", sa.Integer()),
            sa.Column("sold_30d", sa.Integer()), sa.Column("sold_prev_30d", sa.Integer()),
            sa.Column("competition", sa.String(10)), sa.Column("return_rate", sa.Float()),
            sa.Column("video_fit", sa.Float()), _ts("data_updated_at", True), _ts("imported_at"),
            sa.Column("source", sa.String(10), nullable=False, server_default="csv"),
            sa.Column("source_label", sa.String(200)),
            sa.Column("is_favorite", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.UniqueConstraint("platform", "external_id", name="uq_platform_external"),
        )
        op.create_index("ix_products_platform", "products", ["platform"])
        op.create_index("ix_products_name", "products", ["name"])
        op.create_index("ix_products_category", "products", ["category"])
        op.create_index("ix_products_source", "products", ["source"])
    if "app_settings" not in existing:
        op.create_table("app_settings", sa.Column("key", sa.String(60), primary_key=True),
                        sa.Column("value", sa.JSON(), nullable=False), _ts("updated_at"))
    if "import_logs" not in existing:
        op.create_table("import_logs", _pk(), sa.Column("filename", sa.String(300), nullable=False),
                        sa.Column("created", sa.Integer(), nullable=False), sa.Column("updated", sa.Integer(), nullable=False),
                        sa.Column("rejected", sa.Integer(), nullable=False), sa.Column("errors", sa.Text()), _ts())

    # Cột mới của products (cả với database cũ lẫn mới: chỉ thêm khi thiếu)
    have = {c["name"] for c in sa.inspect(op.get_bind()).get_columns("products")}
    for name, typ in (("shop_name", sa.String(200)), ("seller_rating", sa.Float()), ("commission_amount", sa.Float()),
                      ("country", sa.String(2)), ("created_at", sa.DateTime()), ("updated_at", sa.DateTime())):
        if name not in have:
            op.add_column("products", sa.Column(name, typ, nullable=True))
    # DEMO nay nằm ở database riêng: xóa bản DEMO cũ còn lẫn trong database thật.
    op.execute("DELETE FROM products WHERE source = 'demo'")

    op.create_table("users", _pk(), sa.Column("username", sa.String(60), nullable=False, unique=True),
                    sa.Column("display_name", sa.String(120)), _ts())
    op.create_table(
        "marketplace_connections", _pk(), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("marketplace", sa.String(20), nullable=False),
        sa.Column("connection_status", sa.String(20), nullable=False, server_default="not_linked"),
        sa.Column("access_token_encrypted", sa.Text()), sa.Column("refresh_token_encrypted", sa.Text()),
        _ts("token_expires_at", True), sa.Column("scopes", sa.Text()), _ts("last_sync_at", True),
        sa.Column("last_error", sa.Text()), _ts(), _ts("updated_at"),
        sa.UniqueConstraint("user_id", "marketplace", name="uq_user_marketplace"),
    )
    op.create_table(
        "product_snapshots", _pk(),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("price", sa.Float()), sa.Column("commission_rate", sa.Float()), sa.Column("rating", sa.Float()),
        sa.Column("review_count", sa.Integer()), sa.Column("sales_count", sa.Integer()), _ts("captured_at"))
    op.create_index("ix_product_snapshots_product_id", "product_snapshots", ["product_id"])
    op.create_table(
        "affiliate_links", _pk(),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False), sa.Column("source", sa.String(20), nullable=False), _ts())
    op.create_index("ix_affiliate_links_product_id", "affiliate_links", ["product_id"])
    op.create_table(
        "product_scores", _pk(),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Float()), sa.Column("confidence", sa.Float()), sa.Column("breakdown", sa.JSON()),
        sa.Column("formula_version", sa.String(20), nullable=False), _ts("computed_at"))
    op.create_index("ix_product_scores_product_id", "product_scores", ["product_id"])
    op.create_table(
        "scan_jobs", _pk(), sa.Column("marketplace", sa.String(20), nullable=False),
        sa.Column("status", sa.String(20), nullable=False), sa.Column("params", sa.JSON()),
        sa.Column("max_products", sa.Integer(), nullable=False), sa.Column("products_found", sa.Integer(), nullable=False),
        sa.Column("requests_made", sa.Integer(), nullable=False), sa.Column("resume_cursor", sa.JSON()),
        sa.Column("error", sa.Text()), _ts(), _ts("started_at", True), _ts("finished_at", True))
    op.create_table(
        "scan_results", _pk(),
        sa.Column("scan_job_id", sa.Integer(), sa.ForeignKey("scan_jobs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="SET NULL")),
        sa.Column("external_id", sa.String(120)), sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("message", sa.Text()), _ts())
    op.create_index("ix_scan_results_scan_job_id", "scan_results", ["scan_job_id"])
    op.create_table(
        "ai_analysis", _pk(),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False), sa.Column("model", sa.String(80)),
        sa.Column("kind", sa.String(30), nullable=False), sa.Column("result", sa.JSON()),
        sa.Column("status", sa.String(20), nullable=False), _ts())
    op.create_index("ix_ai_analysis_product_id", "ai_analysis", ["product_id"])
    op.create_table(
        "api_usage_logs", _pk(), sa.Column("service", sa.String(30), nullable=False), sa.Column("endpoint", sa.String(200)),
        sa.Column("status_code", sa.Integer()), sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("error_code", sa.String(60)), sa.Column("latency_ms", sa.Integer()), _ts())
    op.create_index("ix_api_usage_logs_service", "api_usage_logs", ["service"])
    op.create_index("ix_api_usage_logs_created_at", "api_usage_logs", ["created_at"])

    op.execute("INSERT INTO users (username, display_name, created_at) VALUES ('local', 'Người dùng cục bộ', CURRENT_TIMESTAMP)")


def downgrade() -> None:
    for t in ("api_usage_logs", "ai_analysis", "scan_results", "scan_jobs", "product_scores",
              "affiliate_links", "product_snapshots", "marketplace_connections", "users"):
        op.drop_table(t)
    with op.batch_alter_table("products") as b:
        for c in ("shop_name", "seller_rating", "commission_amount", "country", "created_at", "updated_at"):
            b.drop_column(c)
