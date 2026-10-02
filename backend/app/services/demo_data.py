"""Dữ liệu DEMO — sản phẩm HOÀN TOÀN HƯ CẤU, chỉ để trải nghiệm giao diện.
Mọi số liệu ở đây không phải dữ liệu thị trường thật. Một số trường cố ý để trống
để minh họa trạng thái 'Chưa có dữ liệu'."""
from datetime import timedelta

from ..models import Product, utcnow

# (platform, tên, ngành, giá, hoa hồng %, rating, số đánh giá, tổng bán, bán 30d, 30d trước, cạnh tranh, hoàn %, video_fit)
_ROWS = [
    ("shopee", "Máy xay mini cầm tay", "Gia dụng", 289000, 9, 4.7, 3200, 15400, 1800, 1200, "high", 4, 4),
    ("shopee", "Đèn bàn LED chống cận", "Gia dụng", 199000, 8, 4.8, 5100, 28000, 2100, 2400, "high", 3, 3),
    ("tiktok_shop", "Kem chống nắng dạng xịt", "Làm đẹp", 249000, 15, 4.5, 860, 6200, 1500, 600, "medium", 7, 5),
    ("tiktok_shop", "Tai nghe bluetooth mini", "Điện tử", 359000, 6, 4.3, 2400, 12000, 900, 1100, "high", 9, 4),
    ("shopee", "Bình giữ nhiệt 750ml", "Gia dụng", 229000, 12, 4.9, 8700, 41000, 3000, 2500, "medium", 2, 3),
    ("tiktok_shop", "Combo kẹp tóc phong cách Hàn", "Thời trang", 79000, 18, 4.6, 420, 3100, 800, 300, "low", 5, 5),
    ("shopee", "Giá treo đồ đa năng không khoan tường", "Gia dụng", 119000, 14, 4.6, 1900, 9800, 1100, 700, "low", 4, 4),
    ("tiktok_shop", "Serum dưỡng ẩm 30ml", "Làm đẹp", 329000, 20, 4.4, 150, 900, 400, None, None, None, 4),
    ("shopee", "Bàn phím cơ không dây", "Điện tử", 790000, 5, 4.6, 640, 2800, 250, 260, "medium", 3, 3),
    ("tiktok_shop", "Áo thun cotton basic", "Thời trang", 149000, 10, 3.8, 95, 700, 200, 350, "high", 14, 2),
    ("shopee", "Nồi chiên không dầu 5L", "Gia dụng", 1290000, 4, 4.8, 12000, 33000, 2500, 2000, "high", 3, 4),
    ("tiktok_shop", "Dụng cụ lăn tẩy lông thú cưng", "Thú cưng", 99000, 16, 4.5, None, None, None, None, None, None, 5),
    ("shopee", "Ốp lưng điện thoại trong suốt", "Phụ kiện", 49000, 7, 4.2, 15000, 120000, 6000, 7000, "high", 6, 2),
    ("shopee", "Gấu bông len thủ công", "Quà tặng", 159000, 11, None, None, 300, None, None, "low", None, 4),
    ("tiktok_shop", "Máy massage cổ vai gáy", "Sức khỏe", 459000, 13, 4.2, 1100, 5400, 700, 900, "medium", 11, 4),
]


def build_demo() -> list[Product]:
    now = utcnow()
    out = []
    for i, r in enumerate(_ROWS, start=1):
        plat, name, cat, price, comm, rating, rv, sold, s30, sp30, comp, ret, vf = r
        out.append(Product(
            platform=plat, external_id=f"demo-{i:03d}", name=f"[DEMO] {name}", category=cat, price=price,
            currency="VND", commission_rate=comm, rating=rating, review_count=rv, sold_count=sold,
            sold_30d=s30, sold_prev_30d=sp30, competition=comp, return_rate=ret, video_fit=vf,
            data_updated_at=now - timedelta(days=i % 9), source="demo", source_label="Dữ liệu DEMO hư cấu",
            imported_at=now,
        ))
    return out
