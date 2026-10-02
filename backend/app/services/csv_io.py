"""Nhập/xuất CSV có kiểm tra dữ liệu từng dòng."""
from __future__ import annotations

import csv
import hashlib
import io
import re
import unicodedata
from datetime import datetime

from sqlalchemy.orm import Session

from ..models import ImportLog, Product, utcnow

PLATFORMS = {"shopee": "shopee", "tiktok": "tiktok_shop", "tiktokshop": "tiktok_shop", "tiktok_shop": "tiktok_shop",
             "tiktok shop": "tiktok_shop"}
COMPETITION = {"low": "low", "thap": "low", "medium": "medium", "trung binh": "medium", "high": "high", "cao": "high"}

# tên cột chuẩn -> các tên chấp nhận (đã chuẩn hóa không dấu, chữ thường)
ALIASES = {
    "platform": ["platform", "nen tang", "san"],
    "external_id": ["external_id", "id", "ma san pham", "product_id", "sku"],
    "name": ["name", "ten", "ten san pham", "product_name", "title"],
    "url": ["url", "link", "lien ket", "affiliate_link"],
    "image_url": ["image_url", "image", "anh", "hinh anh"],
    "category": ["category", "nganh hang", "danh muc"],
    "price": ["price", "gia", "gia ban"],
    "currency": ["currency", "tien te"],
    "commission_rate": ["commission_rate", "commission", "hoa hong", "ty le hoa hong", "hoa hong %"],
    "rating": ["rating", "danh gia", "diem danh gia"],
    "review_count": ["review_count", "reviews", "so danh gia", "so luong danh gia"],
    "positive_review_pct": ["positive_review_pct", "danh gia tich cuc %", "ty le tich cuc"],
    "negative_review_pct": ["negative_review_pct", "danh gia tieu cuc %", "ty le tieu cuc"],
    "sold_count": ["sold_count", "sold", "da ban", "so luong ban"],
    "sold_30d": ["sold_30d", "ban 30 ngay"],
    "sold_prev_30d": ["sold_prev_30d", "ban 30 ngay truoc"],
    "competition": ["competition", "canh tranh", "muc do canh tranh"],
    "return_rate": ["return_rate", "ty le hoan", "ty le hoan huy"],
    "video_fit": ["video_fit", "phu hop video"],
    "data_updated_at": ["data_updated_at", "updated_at", "ngay cap nhat", "cap nhat"],
}
TEMPLATE_COLUMNS = list(ALIASES.keys())
TEMPLATE_EXAMPLE = {
    "platform": "shopee", "external_id": "SP-0001", "name": "Tên sản phẩm của bạn", "url": "https://...",
    "category": "Gia dụng", "price": "199000", "currency": "VND", "commission_rate": "8", "rating": "4.7",
    "review_count": "1200", "sold_count": "5000", "competition": "medium", "data_updated_at": "2025-01-31",
}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.strip().lower().replace("đ", "d"))
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"[\s\-]+", " ", s)


_ALIAS_MAP = {norm(a): k for k, al in ALIASES.items() for a in al}


def _to_float(t: str) -> float:
    """Đọc số kiểu 1,234.5 / 1.234,5 / 199.000 (VN) / 4,5."""
    if "," in t and "." in t:
        return float(t.replace(",", "") if t.rfind(".") > t.rfind(",") else t.replace(".", "").replace(",", "."))
    if "," in t:
        head, tail = t.rsplit(",", 1)
        return float(t.replace(",", "")) if len(tail) == 3 and head else float(t.replace(",", "."))
    return float(t)


def _num(v: str, name: str, lo=None, hi=None, integer=False):
    v = v.strip()
    if v == "":
        return None
    t = v.replace(" ", "").replace("%", "").replace("₫", "")
    if hi is None and re.fullmatch(r"\d{1,3}(\.\d{3})+", t):  # 199.000 -> 199000 (kiểu VN)
        t = t.replace(".", "")
    try:
        x = _to_float(t)
    except ValueError:
        raise ValueError(f"'{name}' phải là số (nhận '{v}')")
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError(f"'{name}' không hợp lệ")
    if lo is not None and x < lo or hi is not None and x > hi:
        raise ValueError(f"'{name}' phải trong khoảng {lo}–{hi} (nhận {x:g})")
    return int(round(x)) if integer else x


def _date(v: str):
    v = v.strip()
    if not v:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(v, fmt)
        except ValueError:
            pass
    raise ValueError(f"'data_updated_at' sai định dạng (dùng YYYY-MM-DD hoặc DD/MM/YYYY, nhận '{v}')")


def parse_row(raw: dict[str, str]) -> dict:
    d: dict = {}
    platform = PLATFORMS.get(norm(raw.get("platform", "")))
    if not platform:
        raise ValueError("'platform' phải là shopee hoặc tiktok_shop")
    d["platform"] = platform
    name = raw.get("name", "").strip()
    if not name:
        raise ValueError("thiếu 'name' (tên sản phẩm)")
    d["name"] = name[:300]
    for f in ("url", "image_url"):
        v = raw.get(f, "").strip()
        if v and not re.match(r"^https?://", v, re.I):
            raise ValueError(f"'{f}' phải bắt đầu bằng http:// hoặc https://")
        d[f] = v[:1000] or None
    d["category"] = raw.get("category", "").strip()[:120] or None
    cur = raw.get("currency", "").strip().upper() or "VND"
    if not re.match(r"^[A-Z]{3}$", cur):
        raise ValueError("'currency' phải là mã 3 chữ cái (VD: VND)")
    d["currency"] = cur
    d["price"] = _num(raw.get("price", ""), "price", 0)
    d["commission_rate"] = _num(raw.get("commission_rate", ""), "commission_rate", 0, 100)
    d["rating"] = _num(raw.get("rating", ""), "rating", 0, 5)
    d["review_count"] = _num(raw.get("review_count", ""), "review_count", 0, integer=True)
    d["positive_review_pct"] = _num(raw.get("positive_review_pct", ""), "positive_review_pct", 0, 100)
    d["negative_review_pct"] = _num(raw.get("negative_review_pct", ""), "negative_review_pct", 0, 100)
    d["sold_count"] = _num(raw.get("sold_count", ""), "sold_count", 0, integer=True)
    d["sold_30d"] = _num(raw.get("sold_30d", ""), "sold_30d", 0, integer=True)
    d["sold_prev_30d"] = _num(raw.get("sold_prev_30d", ""), "sold_prev_30d", 0, integer=True)
    d["return_rate"] = _num(raw.get("return_rate", ""), "return_rate", 0, 100)
    d["video_fit"] = _num(raw.get("video_fit", ""), "video_fit", 0, 5)
    comp = raw.get("competition", "").strip()
    if comp:
        d["competition"] = COMPETITION.get(norm(comp))
        if not d["competition"]:
            raise ValueError("'competition' phải là low/medium/high (hoặc thấp/trung bình/cao)")
    else:
        d["competition"] = None
    d["data_updated_at"] = _date(raw.get("data_updated_at", ""))
    ext = raw.get("external_id", "").strip()
    if not ext:
        ext = "auto-" + hashlib.sha1((d["url"] or d["name"]).lower().encode()).hexdigest()[:12]
    d["external_id"] = ext[:120]
    return d


def decode(content: bytes) -> str:
    for enc in ("utf-8-sig", "utf-16"):
        try:
            return content.decode(enc)
        except UnicodeDecodeError:
            continue
    raise ValueError("Không đọc được file. Hãy lưu CSV với mã hóa UTF-8.")


def import_csv(db: Session, content: bytes, filename: str, max_rows: int) -> dict:
    text = decode(content)
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.reader(io.StringIO(text), dialect)
    try:
        header = next(reader)
    except StopIteration:
        raise ValueError("File CSV trống.")
    cols = [_ALIAS_MAP.get(norm(h)) for h in header]
    if "name" not in cols or "platform" not in cols:
        raise ValueError("File thiếu cột bắt buộc: platform và name. Hãy tải file mẫu để xem định dạng.")

    created = updated = 0
    errors: list[dict] = []
    seen: set[tuple] = set()
    for i, row in enumerate(reader, start=2):
        if not any(c.strip() for c in row):
            continue
        if i - 1 > max_rows:
            errors.append({"row": i, "message": f"Vượt quá giới hạn {max_rows} dòng, các dòng sau bị bỏ qua."})
            break
        raw = {}
        for c, v in zip(cols, row):
            if c and c not in raw:
                raw[c] = v
        try:
            d = parse_row(raw)
        except ValueError as e:
            errors.append({"row": i, "message": str(e)})
            continue
        key = (d["platform"], d["external_id"])
        if key in seen:
            errors.append({"row": i, "message": "Trùng ID sản phẩm trong cùng file, dòng này bị bỏ qua."})
            continue
        seen.add(key)
        existing = db.query(Product).filter_by(platform=d["platform"], external_id=d["external_id"]).first()
        if existing and existing.source == "demo":
            errors.append({"row": i, "message": "ID trùng với sản phẩm DEMO; hãy đổi ID hoặc xóa dữ liệu DEMO."})
            continue
        if existing:
            for k, v in d.items():
                setattr(existing, k, v)
            existing.source, existing.source_label, existing.imported_at = "csv", filename, utcnow()
            updated += 1
        else:
            db.add(Product(**d, source="csv", source_label=filename, imported_at=utcnow()))
            created += 1
    db.add(ImportLog(filename=filename, created=created, updated=updated, rejected=len(errors),
                     errors="; ".join(f"dòng {e['row']}: {e['message']}" for e in errors[:50]) or None))
    db.commit()
    return {"created": created, "updated": updated, "rejected": len(errors), "errors": errors[:100]}


def _safe(v):
    """Chống CSV injection khi mở bằng Excel."""
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def export_csv(products: list[Product]) -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(TEMPLATE_COLUMNS + ["source"])
    for p in products:
        w.writerow([_safe(p.data_updated_at.strftime("%Y-%m-%d") if c == "data_updated_at" and p.data_updated_at
                          else ("" if getattr(p, c) is None or c == "data_updated_at" else getattr(p, c)))
                    for c in TEMPLATE_COLUMNS] + [p.source])
    return "﻿" + buf.getvalue()


def template_csv() -> str:
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(TEMPLATE_COLUMNS)
    w.writerow([TEMPLATE_EXAMPLE.get(c, "") for c in TEMPLATE_COLUMNS])
    return "﻿" + buf.getvalue()
