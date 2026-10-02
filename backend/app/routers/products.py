from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_data_db, get_db
from ..models import Product, utcnow
from ..services import csv_io
from ..services.app_settings import is_demo_mode
from ..services.scoring import (
    NO_DATA, VIDEO_STYLE_TIPS, commission_per_order, growth_pct, net_commission_estimate, pros_and_risks,
    product_revenue, score_product,
)
from .system import load_settings

router = APIRouter(prefix="/products", tags=["products"])

SORTS = ("score", "commission", "price", "rating", "sold", "growth", "video_fit")


def serialize(p: Product, cfg: dict, detail: bool = False) -> dict:
    r = score_product(p, cfg)
    d = {
        "id": p.id, "platform": p.platform, "name": p.name, "url": p.url, "image_url": p.image_url,
        "category": p.category, "price": p.price, "currency": p.currency, "commission_rate": p.commission_rate,
        "commission_per_order": commission_per_order(p), "rating": p.rating, "review_count": p.review_count,
        "sold_count": p.sold_count, "growth_pct": growth_pct(p), "competition": p.competition,
        "video_fit": p.video_fit, "is_demo": p.is_demo, "source": p.source, "source_label": p.source_label,
        "is_favorite": p.is_favorite,
        "data_updated_at": (p.data_updated_at or p.imported_at).isoformat(),
        "score": r.score, "confidence": r.confidence, "confidence_label": r.confidence_label,
    }
    if detail:
        pros, risks = pros_and_risks(p)
        d.update({
            "external_id": p.external_id, "positive_review_pct": p.positive_review_pct,
            "negative_review_pct": p.negative_review_pct, "sold_30d": p.sold_30d, "sold_prev_30d": p.sold_prev_30d,
            "return_rate": p.return_rate,
            "money": {  # tách bạch các khái niệm tiền
                "nominal_commission_per_order": commission_per_order(p),
                "net_commission_estimate": net_commission_estimate(p),
                "product_revenue": product_revenue(p),
                "estimated_profit": None, "actual_profit": None,
                "notes": {
                    "nominal": "Hoa hồng danh nghĩa = giá × tỷ lệ hoa hồng, chưa trừ hoàn/hủy, thuế, phí.",
                    "net": "Hoa hồng thực nhận ước tính chỉ tính được khi có tỷ lệ hoàn/hủy thật." if p.return_rate is None
                    else "= hoa hồng danh nghĩa × (1 − tỷ lệ hoàn/hủy).",
                    "revenue": "Doanh thu của SẢN PHẨM trên sàn (giá × đã bán), không phải thu nhập của bạn.",
                    "profit": "Lợi nhuận ước tính/thực tế cần chi phí sản xuất video và đơn thật — xem Analytics (Phase 6).",
                },
            },
            "score_breakdown": r.breakdown, "score_raw_average": r.raw_average, "missing": r.missing,
            "explanation": r.explanation, "pros": pros, "risks": risks, "video_tips": VIDEO_STYLE_TIPS,
        })
    return d


def _query(db: Session, platform, category, q, price_min, price_max, commission_min, rating_min, reviews_min,
           sold_min, competition, updated_within_days, source, favorites):
    qs = db.query(Product)
    if platform:
        qs = qs.filter(Product.platform == platform)
    if category:
        qs = qs.filter(Product.category == category)
    if q:
        like = f"%{q.strip()}%"
        qs = qs.filter(or_(Product.name.ilike(like), Product.category.ilike(like)))
    for col, lo, hi in ((Product.price, price_min, price_max),):
        if lo is not None:
            qs = qs.filter(col >= lo)
        if hi is not None:
            qs = qs.filter(col <= hi)
    if commission_min is not None:
        qs = qs.filter(Product.commission_rate >= commission_min)
    if rating_min is not None:
        qs = qs.filter(Product.rating >= rating_min)
    if reviews_min is not None:
        qs = qs.filter(Product.review_count >= reviews_min)
    if sold_min is not None:
        qs = qs.filter(Product.sold_count >= sold_min)
    if competition:
        qs = qs.filter(Product.competition == competition)
    if updated_within_days:
        since = utcnow() - timedelta(days=updated_within_days)
        qs = qs.filter(or_(Product.data_updated_at >= since,
                           (Product.data_updated_at.is_(None)) & (Product.imported_at >= since)))
    if source:
        qs = qs.filter(Product.source == source)
    if favorites:
        qs = qs.filter(Product.is_favorite.is_(True))
    return qs


def filters(
    platform: Literal["shopee", "tiktok_shop"] | None = None, category: str | None = None, q: str | None = None,
    price_min: float | None = Query(None, ge=0), price_max: float | None = Query(None, ge=0),
    commission_min: float | None = Query(None, ge=0, le=100), rating_min: float | None = Query(None, ge=0, le=5),
    reviews_min: int | None = Query(None, ge=0), sold_min: int | None = Query(None, ge=0),
    competition: Literal["low", "medium", "high"] | None = None,
    updated_within_days: int | None = Query(None, ge=1, le=3650),
    source: Literal["demo", "csv", "manual"] | None = None, favorites: bool = False,
):
    if price_min is not None and price_max is not None and price_min > price_max:
        raise HTTPException(422, "Giá tối thiểu không được lớn hơn giá tối đa.")
    return dict(platform=platform, category=category, q=q, price_min=price_min, price_max=price_max,
                commission_min=commission_min, rating_min=rating_min, reviews_min=reviews_min, sold_min=sold_min,
                competition=competition, updated_within_days=updated_within_days, source=source, favorites=favorites)


def _sort_key(item: dict, sort: str):
    v = {"score": item["score"], "commission": item["commission_per_order"], "price": item["price"],
         "rating": item["rating"], "sold": item["sold_count"], "growth": item["growth_pct"],
         "video_fit": item["video_fit"]}[sort]
    return v


def _ranked(db, main, f, sort, order):
    cfg = load_settings(main)
    items = [serialize(p, cfg) for p in _query(db, **f).all()]
    have = [i for i in items if _sort_key(i, sort) is not None]
    none = [i for i in items if _sort_key(i, sort) is None]  # thiếu dữ liệu luôn xếp cuối
    have.sort(key=lambda i: _sort_key(i, sort), reverse=(order == "desc"))
    return have + none


@router.get("")
def list_products(f: dict = Depends(filters), sort: Literal[SORTS] = "score", order: Literal["asc", "desc"] = "desc",
                  page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100), db: Session = Depends(get_data_db),
                  main: Session = Depends(get_db)):
    items = _ranked(db, main, f, sort, order)
    start = (page - 1) * page_size
    return {"total": len(items), "page": page, "page_size": page_size, "items": items[start:start + page_size],
            "no_data_label": NO_DATA}


@router.get("/meta")
def meta(db: Session = Depends(get_data_db)):
    cats = [c for (c,) in db.query(Product.category).distinct().order_by(Product.category) if c]
    return {"categories": cats}


@router.get("/template.csv")
def template():
    return Response(csv_io.template_csv(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="mau-san-pham.csv"'})


@router.get("/export.csv")
def export(f: dict = Depends(filters), sort: Literal[SORTS] = "score", order: Literal["asc", "desc"] = "desc",
           db: Session = Depends(get_data_db), main: Session = Depends(get_db)):
    ids = [i["id"] for i in _ranked(db, main, f, sort, order)]
    by_id = {p.id: p for p in db.query(Product).filter(Product.id.in_(ids)).all()} if ids else {}
    return Response(csv_io.export_csv([by_id[i] for i in ids]), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="san-pham-xuat.csv"'})


@router.post("/import")
async def import_products(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if is_demo_mode(db):
        raise HTTPException(409, "Đang ở chế độ DEMO nên không thể nhập dữ liệu thật. Hãy tắt chế độ DEMO trong Cài đặt.")
    name = (file.filename or "").strip()
    if not name.lower().endswith(".csv"):
        raise HTTPException(415, "Chỉ chấp nhận file .csv")
    limit = settings.max_upload_mb * 1024 * 1024
    content = await file.read(limit + 1)
    if len(content) > limit:
        raise HTTPException(413, f"File quá lớn (tối đa {settings.max_upload_mb} MB).")
    if b"\x00" in content[:4096] and not content.startswith((b"\xff\xfe", b"\xfe\xff")):
        raise HTTPException(415, "File không phải CSV văn bản hợp lệ.")
    try:
        return csv_io.import_csv(db, content, name[:200].replace("/", "_").replace("\\", "_"), settings.max_import_rows)
    except ValueError as e:
        raise HTTPException(422, str(e))


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_data_db), main: Session = Depends(get_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy sản phẩm.")
    return serialize(p, load_settings(main), detail=True)


@router.put("/{product_id}/favorite")
def set_favorite(product_id: int, value: bool = True, db: Session = Depends(get_data_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy sản phẩm.")
    p.is_favorite = value
    db.commit()
    return {"id": p.id, "is_favorite": p.is_favorite}


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_data_db)):
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(404, "Không tìm thấy sản phẩm.")
    db.delete(p)
    db.commit()
    return {"deleted": 1}
