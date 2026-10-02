import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/test.db"
os.environ["DEMO_DATABASE_URL"] = f"sqlite:///{_tmp}/demo.db"
os.environ["LOG_DIR"] = f"{_tmp}/logs"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, demo_engine, engine  # noqa: E402
from app.main import app, run_migrations  # noqa: E402


@pytest.fixture()
def client():
    for e in (engine, demo_engine):
        Base.metadata.drop_all(e)
        with e.begin() as c:
            c.exec_driver_sql("DROP TABLE IF EXISTS alembic_version")
    with TestClient(app) as c:  # lifespan chạy migration + tạo schema demo
        yield c
