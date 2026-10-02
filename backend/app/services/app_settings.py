"""Cài đặt chung của ứng dụng (lưu trong bảng app_settings, khóa 'general')."""
from __future__ import annotations

from sqlalchemy.orm import Session

from ..models import AppSetting

DEFAULTS = {
    "ai_provider": "ollama",
    "ollama_model": "llama3.2:3b",
    "max_products_per_scan": 50,      # thấp mặc định để tránh vượt rate limit
    "max_requests_per_scan": 100,
    "request_delay_seconds": 2.0,
    "retry_count": 3,
    "demo_mode": False,
}
AI_PROVIDERS = {"ollama": True, "openai": False, "gemini": False, "claude": False}  # True = đã triển khai
RANGES = {"max_products_per_scan": (1, 500), "max_requests_per_scan": (1, 1000),
          "request_delay_seconds": (0.5, 60), "retry_count": (0, 10)}


class SettingsError(ValueError):
    pass


def load_general(db: Session) -> dict:
    row = db.get(AppSetting, "general")
    return {**DEFAULTS, **(row.value if row else {})}


def is_demo_mode(db: Session) -> bool:
    return bool(load_general(db)["demo_mode"])


def validate(patch: dict) -> dict:
    out = {}
    for k, v in patch.items():
        if k not in DEFAULTS:
            raise SettingsError(f"Cài đặt không hợp lệ: {k}")
        if k == "ai_provider":
            if v not in AI_PROVIDERS:
                raise SettingsError("Nhà cung cấp AI không hợp lệ.")
            if not AI_PROVIDERS[v]:
                raise SettingsError(f"'{v}' là dịch vụ API có thể tính phí và chưa được triển khai. Hiện chỉ dùng Ollama (local).")
        elif k == "ollama_model":
            if not isinstance(v, str) or not v.strip() or len(v) > 80 or any(c.isspace() for c in v.strip()):
                raise SettingsError("Tên model Ollama không hợp lệ (ví dụ: llama3.2:3b).")
            v = v.strip()
        elif k == "demo_mode":
            if not isinstance(v, bool):
                raise SettingsError("demo_mode phải là true/false.")
        else:
            lo, hi = RANGES[k]
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not lo <= v <= hi:
                raise SettingsError(f"{k} phải là số trong khoảng {lo}–{hi}.")
            if k != "request_delay_seconds":
                v = int(v)
        out[k] = v
    return out


def save_general(db: Session, patch: dict) -> dict:
    clean = validate(patch)
    value = {**load_general(db), **clean}
    row = db.get(AppSetting, "general")
    if row:
        row.value = value
    else:
        db.add(AppSetting(key="general", value=value))
    db.commit()
    return load_general(db)
