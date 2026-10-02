from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import AppSetting, Product
from ..services.demo_data import build_demo
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


@router.post("/demo")
def seed_demo(db: Session = Depends(get_db)):
    if db.query(Product).filter_by(source="demo").count():
        raise HTTPException(409, "Dữ liệu DEMO đã được nạp.")
    items = build_demo()
    db.add_all(items)
    db.commit()
    return {"created": len(items)}


@router.delete("/demo")
def delete_demo(db: Session = Depends(get_db)):
    n = db.query(Product).filter_by(source="demo").delete()
    db.commit()
    return {"deleted": n}


@router.delete("/data")
def delete_all_user_data(db: Session = Depends(get_db)):
    """Xóa toàn bộ sản phẩm do người dùng nhập (CSV/thủ công), giữ nguyên dữ liệu DEMO."""
    n = db.query(Product).filter(Product.source != "demo").delete()
    db.commit()
    return {"deleted": n}


@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    by_source = dict(db.query(Product.source, func.count()).group_by(Product.source).all())
    by_platform = dict(db.query(Product.platform, func.count()).group_by(Product.platform).all())
    return {"total": sum(by_source.values()), "by_source": by_source, "by_platform": by_platform,
            "favorites": db.query(Product).filter_by(is_favorite=True).count()}


INTEGRATIONS = [
    {"key": "csv", "name": "Nhập CSV", "platform": "shopee,tiktok_shop", "status": "available",
     "note": "Hoạt động. Dùng khi bạn xuất dữ liệu từ trang đối tác/affiliate của sàn."},
    {"key": "shopee_affiliate", "name": "Shopee Affiliate (API)", "platform": "shopee", "status": "not_connected",
     "note": "Phase 2. Cần tài khoản Shopee Affiliate được duyệt và thông tin API do Shopee cấp. "
             "Chưa xác minh quyền truy cập nên chưa triển khai."},
    {"key": "tiktok_shop_affiliate", "name": "TikTok Shop Affiliate (API)", "platform": "tiktok_shop",
     "status": "not_connected",
     "note": "Phase 2. Cần tài khoản TikTok Shop Partner/Affiliate được duyệt. Chưa xác minh nên chưa triển khai."},
    {"key": "ai_provider", "name": "AI viết kịch bản (Claude/Gemini)", "platform": "-", "status": "not_connected",
     "note": "Phase 3. Cần API key của bạn (có phí theo mức dùng). Chưa dùng trong Phase 1."},
    {"key": "veo", "name": "Google Flow / Veo", "platform": "-", "status": "not_connected",
     "note": "Phase 5. Cần xác minh API chính thức, quyền truy cập và chi phí trước khi tích hợp."},
    {"key": "seedance", "name": "Seedance", "platform": "-", "status": "not_connected",
     "note": "Phase 5. Cần xác minh API chính thức và quyền sử dụng thương mại trước khi tích hợp."},
]


@router.get("/integrations")
def integrations():
    return INTEGRATIONS
