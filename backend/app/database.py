from sqlalchemy import create_engine
from fastapi import Depends
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import BASE_DIR, settings

if settings.database_url.startswith("sqlite"):
    (BASE_DIR / "data").mkdir(exist_ok=True)

def _make_engine(url: str):
    args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=args)


engine = _make_engine(settings.database_url)  # dữ liệu THẬT
SessionLocal = sessionmaker(bind=engine, autoflush=False)
# Dữ liệu DEMO nằm trong file riêng, không bao giờ trộn với database thật.
demo_engine = _make_engine(settings.demo_database_url)
DemoSessionLocal = sessionmaker(bind=demo_engine, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_data_db(db: Session = Depends(get_db)):
    """Session cho dữ liệu sản phẩm: database thật, hoặc database DEMO khi bật chế độ DEMO."""
    from .services.app_settings import is_demo_mode

    if is_demo_mode(db):
        demo = DemoSessionLocal()
        try:
            yield demo
        finally:
            demo.close()
    else:
        yield db
