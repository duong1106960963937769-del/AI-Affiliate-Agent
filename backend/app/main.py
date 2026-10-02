import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError  # noqa: F401
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from mock.demo_seed import ensure_demo_schema

from .config import BASE_DIR, settings
from .logging_setup import setup_logging
from .routers import connections, monitor, products, system

app_log, api_log, err_log = logging.getLogger("app"), logging.getLogger("api"), logging.getLogger("error")


def run_migrations() -> None:
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))
    command.upgrade(cfg, "head")


@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging(settings.log_dir)
    run_migrations()
    ensure_demo_schema()
    app_log.info("Ứng dụng khởi động; database và migration sẵn sàng")
    yield


app = FastAPI(title="AI Affiliate Agent API", version="0.2.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def access_log(request: Request, call_next):
    t0 = time.monotonic()
    try:
        resp = await call_next(request)
    except Exception:
        err_log.exception("Lỗi không xử lý: %s %s", request.method, request.url.path)
        return JSONResponse(status_code=500, content={
            "detail": "Đã xảy ra lỗi không mong muốn. Vui lòng thử lại. Chi tiết kỹ thuật đã được ghi vào logs/error.log."})
    api_log.info("%s %s -> %s (%d ms)", request.method, request.url.path, resp.status_code, (time.monotonic() - t0) * 1000)
    return resp


app.include_router(products.router, prefix="/api")
app.include_router(system.router, prefix="/api")
app.include_router(connections.router, prefix="/api")
app.include_router(monitor.router, prefix="/api")
