"""Nạp dữ liệu DEMO vào database DEMO riêng (không bao giờ vào database thật)."""
from sqlalchemy import inspect
from sqlalchemy.orm import Session

from app.database import Base, demo_engine
from app.models import Product

from .demo_products import build_demo


def ensure_demo_schema() -> None:
    """Database DEMO dùng một lần: nếu cấu trúc cũ so với models thì xóa và tạo lại."""
    insp = inspect(demo_engine)
    if insp.has_table("products"):
        have = {c["name"] for c in insp.get_columns("products")}
        if not set(Product.__table__.columns.keys()) <= have:
            Base.metadata.drop_all(demo_engine)
    Base.metadata.create_all(demo_engine)


def seed_demo(db: Session) -> int:
    if db.query(Product).count():
        return 0
    items = build_demo()
    db.add_all(items)
    db.commit()
    return len(items)


def reset_demo(db: Session) -> int:
    db.query(Product).delete()
    db.commit()
    return seed_demo(db)
