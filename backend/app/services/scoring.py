"""Product Opportunity Score (0-100) — công thức minh bạch, giải thích được.

Nguyên tắc:
- Mỗi tiêu chí có điểm con 0-100, chỉ tính khi sản phẩm CÓ dữ liệu cho tiêu chí đó.
- Điểm trung bình có trọng số chỉ tính trên các tiêu chí có dữ liệu.
- Độ tin cậy = tổng trọng số các tiêu chí có dữ liệu / tổng trọng số.
- Điểm cuối = điểm trung bình * (0.6 + 0.4 * độ tin cậy): thiếu dữ liệu thì bị trừ điểm.
- Không bao giờ tự bịa số liệu cho tiêu chí thiếu.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from ..models import Product

CRITERIA: dict[str, dict] = {
    "commission": {"label": "Hoa hồng trên đơn", "weight": 20,
                   "hint": "Hoa hồng danh nghĩa/đơn so với mức mục tiêu trong Settings"},
    "rating": {"label": "Điểm đánh giá", "weight": 12, "hint": "3★ = 0 điểm, 5★ = 100 điểm"},
    "reviews": {"label": "Số lượng đánh giá", "weight": 8, "hint": "Thang log, 10.000 đánh giá = 100 điểm"},
    "sales": {"label": "Số lượng bán", "weight": 15, "hint": "Thang log, 100.000 đã bán = 100 điểm"},
    "growth": {"label": "Tốc độ tăng trưởng", "weight": 12,
               "hint": "So sánh bán 30 ngày gần nhất với 30 ngày trước đó; 0% = 50 điểm"},
    "competition": {"label": "Mức độ cạnh tranh", "weight": 10, "hint": "Thấp = 100, Trung bình = 55, Cao = 15"},
    "video_fit": {"label": "Phù hợp làm video", "weight": 10, "hint": "Điểm 0-5 do bạn đánh giá"},
    "sentiment": {"label": "Tỷ lệ đánh giá tích cực", "weight": 8, "hint": "% đánh giá tích cực"},
    "quality_risk": {"label": "Rủi ro hoàn/hủy", "weight": 5, "hint": "Tỷ lệ hoàn/hủy càng thấp càng tốt (20% = 0 điểm)"},
}

DEFAULT_SETTINGS = {
    "weights": {k: v["weight"] for k, v in CRITERIA.items()},
    "commission_target": 50000.0,  # VND/đơn tương ứng 100 điểm
}

NO_DATA = "Chưa có dữ liệu"


def clamp(x: float, lo: float = 0, hi: float = 100) -> float:
    return max(lo, min(hi, x))


def log_scale(n: float, cap: float) -> float:
    return clamp(math.log10(n + 1) / math.log10(cap + 1) * 100)


def commission_per_order(p: Product) -> float | None:
    """Hoa hồng DANH NGHĨA trên một đơn (giá x tỷ lệ). Chưa trừ hoàn/hủy, thuế, phí."""
    if p.price is None or p.commission_rate is None:
        return None
    return round(p.price * p.commission_rate / 100, 2)


def net_commission_estimate(p: Product) -> float | None:
    """Hoa hồng thực nhận ước tính: chỉ tính khi có tỷ lệ hoàn/hủy thật."""
    nominal = commission_per_order(p)
    if nominal is None or p.return_rate is None:
        return None
    return round(nominal * (1 - p.return_rate / 100), 2)


def growth_pct(p: Product) -> float | None:
    if p.sold_30d is None or not p.sold_prev_30d:
        return None
    return round((p.sold_30d - p.sold_prev_30d) / p.sold_prev_30d * 100, 1)


def product_revenue(p: Product) -> float | None:
    """Doanh thu CỦA SẢN PHẨM trên sàn (giá x đã bán) — không phải thu nhập của bạn."""
    if p.price is None or p.sold_count is None:
        return None
    return round(p.price * p.sold_count, 2)


def _criterion_scores(p: Product, settings: dict) -> dict[str, float | None]:
    nominal = commission_per_order(p)
    g = growth_pct(p)
    target = float(settings.get("commission_target") or DEFAULT_SETTINGS["commission_target"])
    sentiment = p.positive_review_pct
    if sentiment is None and p.negative_review_pct is not None:
        sentiment = 100 - p.negative_review_pct
    return {
        "commission": None if nominal is None else clamp(nominal / target * 100),
        "rating": None if p.rating is None else clamp((p.rating - 3) / 2 * 100),
        "reviews": None if p.review_count is None else log_scale(p.review_count, 10_000),
        "sales": None if p.sold_count is None else log_scale(p.sold_count, 100_000),
        "growth": None if g is None else clamp(50 + g / 2),
        "competition": {"low": 100.0, "medium": 55.0, "high": 15.0}.get(p.competition or ""),
        "video_fit": None if p.video_fit is None else clamp(p.video_fit * 20),
        "sentiment": None if sentiment is None else clamp(sentiment),
        "quality_risk": None if p.return_rate is None else clamp(100 - p.return_rate * 5),
    }


@dataclass
class ScoreResult:
    score: float | None
    raw_average: float | None
    confidence: float
    confidence_label: str
    breakdown: list[dict]
    missing: list[str]
    explanation: str


def confidence_label(c: float) -> str:
    return "Cao" if c >= 0.8 else "Trung bình" if c >= 0.5 else "Thấp"


def score_product(p: Product, settings: dict | None = None) -> ScoreResult:
    settings = settings or DEFAULT_SETTINGS
    weights = {**DEFAULT_SETTINGS["weights"], **settings.get("weights", {})}
    scores = _criterion_scores(p, settings)
    total_w = sum(max(0, weights[k]) for k in CRITERIA) or 1
    avail_w = sum(max(0, weights[k]) for k in CRITERIA if scores[k] is not None)

    breakdown, missing = [], []
    for k, meta in CRITERIA.items():
        s = scores[k]
        w = max(0, weights[k])
        breakdown.append({
            "key": k, "label": meta["label"], "hint": meta["hint"], "weight": w,
            "score": None if s is None else round(s, 1),
            "contribution": None if s is None or not avail_w else round(s * w / avail_w, 1),
            "display": NO_DATA if s is None else f"{s:.0f}/100",
        })
        if s is None:
            missing.append(meta["label"])

    if avail_w == 0:
        return ScoreResult(None, None, 0.0, "Thấp", breakdown, missing,
                           "Chưa đủ dữ liệu để chấm điểm: không có tiêu chí nào có số liệu.")

    avg = sum(scores[k] * max(0, weights[k]) for k in CRITERIA if scores[k] is not None) / avail_w
    conf = avail_w / total_w
    final = avg * (0.6 + 0.4 * conf)
    expl = (f"Điểm trung bình có trọng số trên {len(CRITERIA) - len(missing)}/{len(CRITERIA)} tiêu chí có dữ liệu "
            f"là {avg:.1f}. Độ tin cậy dữ liệu {conf * 100:.0f}% nên điểm cuối = {avg:.1f} × "
            f"(0,6 + 0,4 × {conf:.2f}) = {final:.1f}.")
    if missing:
        expl += " Thiếu dữ liệu: " + ", ".join(missing) + "."
    return ScoreResult(round(final, 1), round(avg, 1), round(conf, 2), confidence_label(conf), breakdown, missing, expl)


def pros_and_risks(p: Product) -> tuple[list[str], list[str]]:
    """Ưu điểm/rủi ro suy ra TRỰC TIẾP từ số liệu có sẵn, không thêm nhận định ngoài dữ liệu."""
    pros, risks = [], []
    nominal = commission_per_order(p)
    if nominal is not None and nominal >= 30000:
        pros.append(f"Hoa hồng danh nghĩa khoảng {nominal:,.0f} {p.currency}/đơn.")
    if p.rating is not None and p.review_count is not None:
        if p.rating >= 4.5 and p.review_count >= 500:
            pros.append(f"Đánh giá {p.rating}★ từ {p.review_count:,} lượt.")
        elif p.rating < 4.0:
            risks.append(f"Điểm đánh giá thấp ({p.rating}★).")
        if p.review_count < 50:
            risks.append(f"Mới có {p.review_count} đánh giá — chưa đủ để kết luận về chất lượng.")
    g = growth_pct(p)
    if g is not None:
        (pros if g >= 20 else risks if g <= -20 else []).append(f"Doanh số 30 ngày thay đổi {g:+.0f}% so với kỳ trước.")
    if p.competition == "low":
        pros.append("Mức cạnh tranh thấp (theo dữ liệu bạn cung cấp).")
    if p.competition == "high":
        risks.append("Mức cạnh tranh cao (theo dữ liệu bạn cung cấp).")
    if p.return_rate is not None and p.return_rate >= 8:
        risks.append(f"Tỷ lệ hoàn/hủy {p.return_rate:.0f}% làm giảm hoa hồng thực nhận.")
    if p.negative_review_pct is not None and p.negative_review_pct >= 15:
        risks.append(f"{p.negative_review_pct:.0f}% đánh giá tiêu cực.")
    if p.commission_rate is None:
        risks.append("Chưa có tỷ lệ hoa hồng — không thể ước tính thu nhập.")
    if not p.url:
        risks.append("Chưa có liên kết sản phẩm.")
    return pros, risks


VIDEO_STYLE_TIPS = [
    "UGC: người thật giới thiệu cách dùng sản phẩm trong tình huống đời thường.",
    "Problem/Solution: nêu vấn đề phổ biến rồi cho thấy sản phẩm xử lý ra sao.",
    "Product demonstration: quay cận cảnh tính năng thực tế của sản phẩm.",
    "Unboxing: mở hộp, giới thiệu những gì có trong hộp.",
    "Lưu ý: chỉ nêu công dụng đúng mô tả của người bán; không bịa trải nghiệm hay kết quả.",
]
