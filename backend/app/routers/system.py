from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import DemoSessionLocal, get_data_db, get_db
from ..models import AppSetting, Product
from mock.demo_seed import ensure_demo_schema, reset_demo, seed_demo
from ..services.app_settings import SettingsError, is_demo_mode, load_general, save_general
from ..services.scoring import CRITERIA, DEFAULT_SETTINGS

router = APIRouter()


def load_settings(db: Session) -> dict:
    row = db.get(AppSetting, "scoring")
    if not row:
        return DEFAULT_SETTINGS
    return {"weights": {**DEFAULT_SETTINGS["weights"], **row.value.get("weights", {})},
            "commission_target": row.value.get("commission_target", DEFAULT_SETTINGS["commission_target"])}


class SettingsIn(BaseModel):
    weights: dict[str, float]
    commission_target: float = Field(gt=0, le=1e9)


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return {**load_settings(db), "criteria": [{"key": k, "label": v["label"], "hint": v["hint"]} for k, v in CRITERIA.items()]}


@router.put("/settings")
def put_settings(body: SettingsIn, db: Session = Depends(get_db)):
    unknown = set(body.weights) - set(CRITERIA)
    if unknown:
        raise HTTPException(422, f"Tiêu chí không hợp lệ: {', '.join(sorted(unknown))}")
    if any(w < 0 or w > 100 for w in body.weights.values()):
        raise HTTPException(422, "Trọng số phải từ 0 đến 100.")
    merged = {**DEFAULT_SETTINGS["weights"], **body.weights}
    if sum(merged.values()) <= 0:
        raise HTTPException(422, "Tổng trọng số phải lớn hơn 0.")
    value = {"weights": merged, "commission_target": body.commission_target}
    row = db.get(AppSetting, "scoring")
    if row:
        row.value = value
    else:
        db.add(AppSetting(key="scoring", value=value))
    db.commit()
    return load_settings(db)


@router.delete("/settings")
def reset_settings(db: Session = Depends(get_db)):
    row = db.get(AppSetting, "scoring")
    if row:
        db.delete(row)
        db.commit()
    return load_settings(db)


@router.get("/settings/general")
def get_general(db: Session = Depends(get_db)):
    return load_general(db)


@router.put("/settings/general")
def put_general(patch: dict, db: Session = Depends(get_db)):
    try:
        out = save_general(db, patch)
    except SettingsError as e:
        raise HTTPException(422, str(e))
    if out["demo_mode"]:  # lần đầu bật DEMO thì nạp dữ liệu vào database DEMO riêng
        ensure_demo_schema()
        with DemoSessionLocal() as demo:
            seed_demo(demo)
    return out


@router.post("/demo/reset")
def reset_demo_data():
    """Đặt lại database DEMO (không đụng tới dữ liệu thật)."""
    ensure_demo_schema()
    with DemoSessionLocal() as demo:
        return {"created": reset_demo(demo)}


@router.delete("/data")
def delete_all_user_data(db: Session = Depends(get_db)):
    """Xóa toàn bộ sản phẩm THẬT do người dùng nhập. Không áp dụng trong chế độ DEMO."""
    if is_demo_mode(db):
        raise HTTPException(409, "Đang ở chế độ DEMO. Hãy tắt DEMO trước khi xóa dữ liệu thật.")
    n = db.query(Product).delete()
    db.commit()
    return {"deleted": n}


@router.get("/stats")
def stats(db: Session = Depends(get_data_db), main: Session = Depends(get_db)):
    by_source = dict(db.query(Product.source, func.count()).group_by(Product.source).all())
    by_platform = dict(db.query(Product.platform, func.count()).group_by(Product.platform).all())
    return {"mode": "demo" if is_demo_mode(main) else "real", "total": sum(by_source.values()),
            "by_source": by_source, "by_platform": by_platform,
            "favorites": db.query(Product).filter_by(is_favorite=True).count()}
