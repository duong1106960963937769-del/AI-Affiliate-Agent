import os
from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..config import BASE_DIR, settings as env
from ..database import get_db
from ..logging_setup import LOG_FILES, tail_log
from ..models import ApiUsageLog, utcnow
from ..services.ai import AIProviderError, get_provider
from ..services.app_settings import load_general
from ..services.marketplace import REGISTRY
from ..services.usage import log_api_call
from .connections import _view

router = APIRouter(tags=["monitor"])
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", ""}


@router.post("/ai/test")
def test_ai(db: Session = Depends(get_db)):
    general = load_general(db)
    try:
        provider = get_provider(general)
        h = provider.test_connection()
    except AIProviderError as e:
        log_api_call(db, "ollama", "test_connection", success=False, error_code=e.code)
        return {"ok": False, "code": e.code, "message": e.user_message}
    log_api_call(db, "ollama", "test_connection", success=True, latency_ms=h.latency_ms)
    return {"ok": True, "code": "ok", "message": h.message, "provider": h.provider, "model": h.model,
            "latency_ms": h.latency_ms, "models_installed": h.models_installed}


@router.get("/system/cost")
def cost(db: Session = Depends(get_db)):
    general = load_general(db)
    ai_paid = general["ai_provider"] != "ollama"  # chỉ Ollama được triển khai, nhưng kiểm tra để không báo sai
    db_host = urlparse(env.database_url).hostname if not env.database_url.startswith("sqlite") else None
    cloud_db = bool(db_host) and db_host not in LOCAL_HOSTS
    marketplaces = []
    any_connected = False
    for k in REGISTRY:
        v = _view(db, k)
        any_connected |= v["status"] == "connected"
        marketplaces.append({"marketplace": k, "name": v["name"], "status": v["status"],
                             "cost": {"Confirmed": "Free", "Paid": "Paid"}.get(v["is_free"], "Pricing not confirmed")})
    unknown_mp = any(m["cost"] == "Pricing not confirmed" and m["status"] == "connected" for m in marketplaces)
    if ai_paid or cloud_db or unknown_mp or any(m["cost"] == "Paid" for m in marketplaces):
        monthly, monthly_label = None, "Unknown — có dịch vụ chưa xác nhận giá hoặc trả phí đang được dùng"
    else:
        monthly, monthly_label = 0.0, "$0 (chỉ tính các dịch vụ đang được dùng; hiện không có dịch vụ trả phí nào chạy)"
    return {
        "ai": {"provider": general["ai_provider"], "model": general["ollama_model"],
               "cost_usd": None if ai_paid else 0.0, "label": "Unknown" if ai_paid else "$0 (Ollama chạy trên máy bạn)"},
        "marketplace_api": marketplaces,
        "cloud": {"cost_usd": None if cloud_db else 0.0,
                  "label": "Unknown — database ở máy chủ ngoài" if cloud_db else "$0 (SQLite + lưu trữ cục bộ)"},
        "estimated_monthly_usd": monthly, "estimated_monthly_label": monthly_label,
        "note": "Chi phí điện và Internet của bạn không được tính. Marketplace chưa kết nối thì chưa phát sinh gọi API nào.",
        "any_marketplace_connected": any_connected,
    }


@router.get("/system/usage")
def usage(db: Session = Depends(get_db)):
    now = utcnow()
    day, month = now.replace(hour=0, minute=0, second=0, microsecond=0), now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rows = []
    for service in [*REGISTRY, "ollama"]:
        base = db.query(ApiUsageLog).filter(ApiUsageLog.service == service)
        last = base.order_by(ApiUsageLog.created_at.desc()).first()
        rows.append({
            "service": service,
            "requests_today": base.filter(ApiUsageLog.created_at >= day).count(),
            "requests_month": base.filter(ApiUsageLog.created_at >= month).count(),
            "errors": base.filter(ApiUsageLog.success.is_(False)).count(),
            "last_request": last.created_at.isoformat() if last else None,
            "rate_limit": "Rate limit information unavailable",
            "quota": "Quota information unavailable",
        })
    return rows


@router.get("/system/logs/{name}")
def logs(name: str, lines: int = Query(200, ge=1, le=1000)):
    if name not in LOG_FILES:
        raise HTTPException(404, "Không có log này.")
    return {"name": name, "lines": tail_log(env.log_dir, name, lines)}


@router.get("/system/storage")
def storage(db: Session = Depends(get_db)):
    url = env.database_url
    path = url.replace("sqlite:///", "") if url.startswith("sqlite") else None
    size = os.path.getsize(path) if path and os.path.exists(path) else None
    return {"database": "SQLite" if path else urlparse(url).scheme, "database_path": path, "database_bytes": size,
            "logs_dir": env.log_dir, "log_files": [f"{n}.log" for n in LOG_FILES],
            "uploads_dir": str(BASE_DIR / "data")}
