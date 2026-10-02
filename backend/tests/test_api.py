import io

CSV = (
    "platform,name,price,commission_rate,rating,review_count,sold_count,competition,category\n"
    "shopee,Sản phẩm A,200000,10,4.8,1000,5000,low,Gia dụng\n"
    "tiktok,Sản phẩm B,\"199.000\",15,4.0,50,200,cao,Làm đẹp\n"
    "shopee,,100,5,4,1,1,low,X\n"
    "shopee,Sai hoa hồng,100,150,4,1,1,low,X\n"
    "facebook,Sai sàn,100,5,4,1,1,low,X\n"
    "shopee,=HYPERLINK(\"http://x\"),100,5,,,,,\n"
)


def up(client, content=CSV, name="p.csv"):
    return client.post("/api/products/import", files={"file": (name, io.BytesIO(content.encode()), "text/csv")})


def test_import_validates_rows(client):
    r = up(client).json()
    assert r["created"] == 3 and r["rejected"] == 3
    rows = {e["row"] for e in r["errors"]}
    assert rows == {4, 5, 6}


def test_import_rejects_bad_files(client):
    assert up(client, name="x.exe").status_code == 415
    assert up(client, "a,b\n1,2\n").status_code == 422
    assert up(client, "").status_code == 422


def test_reimport_updates_not_duplicates(client):
    up(client)
    r = up(client).json()
    assert r["created"] == 0 and r["updated"] == 3
    assert client.get("/api/products").json()["total"] == 3


def test_vn_number_format_and_filters(client):
    up(client)
    items = client.get("/api/products", params={"platform": "tiktok_shop"}).json()["items"]
    assert len(items) == 1 and items[0]["price"] == 199000
    assert client.get("/api/products", params={"commission_min": 12}).json()["total"] == 1
    assert client.get("/api/products", params={"competition": "low"}).json()["total"] == 1
    assert client.get("/api/products", params={"q": "sản phẩm a"}).json()["total"] == 1
    assert client.get("/api/products", params={"price_min": 5, "price_max": 1}).status_code == 422
    assert client.get("/api/products", params={"rating_min": 9}).status_code == 422


def test_ranking_sorted_and_missing_last(client):
    up(client)
    items = client.get("/api/products", params={"sort": "rating"}).json()["items"]
    ratings = [i["rating"] for i in items]
    assert ratings[:2] == [4.8, 4.0] and ratings[2] is None


def test_detail_and_favorite(client):
    up(client)
    pid = client.get("/api/products").json()["items"][0]["id"]
    d = client.get(f"/api/products/{pid}").json()
    assert d["money"]["estimated_profit"] is None and d["money"]["actual_profit"] is None
    assert d["score_breakdown"] and d["explanation"]
    assert client.put(f"/api/products/{pid}/favorite").json()["is_favorite"] is True
    assert client.get("/api/products", params={"favorites": True}).json()["total"] == 1
    assert client.get("/api/products/9999").status_code == 404


def test_demo_lifecycle_and_labels(client):
    assert client.get("/api/products").json()["total"] == 0          # DB thật trống
    assert client.put("/api/settings/general", json={"demo_mode": True}).json()["demo_mode"] is True
    items = client.get("/api/products", params={"page_size": 100}).json()["items"]
    assert len(items) == 15 and all(i["is_demo"] and i["name"].startswith("[DEMO]") for i in items)
    assert any(i["score"] is None or i["confidence"] < 0.5 for i in items)  # có sản phẩm thiếu dữ liệu
    assert client.get("/api/stats").json()["mode"] == "demo"
    client.put("/api/settings/general", json={"demo_mode": False})
    assert client.get("/api/products").json()["total"] == 0          # DEMO không lọt vào dữ liệu thật


def test_export_roundtrip_and_injection_guard(client):
    up(client)
    text = client.get("/api/products/export.csv").text
    assert "'=HYPERLINK" in text and "\n=HYPERLINK" not in text
    assert client.get("/api/products/template.csv").status_code == 200


def test_settings_change_scores(client):
    up(client)
    before = client.get("/api/products").json()["items"][0]["score"]
    r = client.put("/api/settings", json={"weights": {"commission": 0, "rating": 100}, "commission_target": 10000})
    assert r.status_code == 200
    after = client.get("/api/products").json()["items"][0]["score"]
    assert before != after
    assert client.put("/api/settings", json={"weights": {"bogus": 1}, "commission_target": 1}).status_code == 422
    assert client.put("/api/settings", json={"weights": {"rating": -1}, "commission_target": 1}).status_code == 422
    assert client.delete("/api/settings").json()["weights"]["commission"] == 20
