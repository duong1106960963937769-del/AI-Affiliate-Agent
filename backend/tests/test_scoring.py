from app.models import Product
from app.services.scoring import commission_per_order, net_commission_estimate, score_product, growth_pct


def mk(**kw):
    return Product(platform="shopee", external_id="x", name="n", currency="VND", **kw)


def test_empty_product_has_no_score():
    r = score_product(mk())
    assert r.score is None and r.confidence == 0
    assert all(b["display"] == "Chưa có dữ liệu" for b in r.breakdown)


def test_commission_is_nominal_and_net_needs_return_rate():
    p = mk(price=200000, commission_rate=10)
    assert commission_per_order(p) == 20000
    assert net_commission_estimate(p) is None
    p.return_rate = 10
    assert net_commission_estimate(p) == 18000


def test_missing_data_lowers_score_and_confidence():
    full = mk(price=500000, commission_rate=10, rating=5, review_count=10000, sold_count=100000,
              sold_30d=200, sold_prev_30d=100, competition="low", video_fit=5,
              positive_review_pct=100, return_rate=0)
    partial = mk(price=500000, commission_rate=10, rating=5)
    f, p = score_product(full), score_product(partial)
    assert f.score == 100 and f.confidence == 1
    assert p.confidence < 0.5 and p.score < p.raw_average


def test_growth_requires_previous_period():
    assert growth_pct(mk(sold_30d=10)) is None
    assert growth_pct(mk(sold_30d=150, sold_prev_30d=100)) == 50


def test_custom_weights():
    p = mk(price=100000, commission_rate=50, rating=3)
    s = {"weights": {"commission": 100, "rating": 0}, "commission_target": 50000}
    assert score_product(p, s).raw_average == 100
