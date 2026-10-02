import io
import logging
import sqlite3

import httpx
import pytest
from alembic import command
from alembic.config import Config

from app.config import BASE_DIR, settings
from app.logging_setup import redact, setup_logging, tail_log
from app.services.ai import AIProviderError, OllamaProvider

CSV = "platform,name,price\nshopee,Thật,100000\n"


def mock_ollama(handler):
    return OllamaProvider("http://ollama.test", "llama3.2:3b", transport=httpx.MockTransport(handler))


# ---------- logging ----------
@pytest.mark.parametrize("raw,secret", [
    ("access_token=abc123xyz", "abc123xyz"), ('{"refresh_token": "r-999"}', "r-999"),
    ("password: hunter2 ok", "hunter2"), ("Authorization: Bearer eyJhbGciOi.payload.sig", "eyJhbGciOi"),
    ("api_key=sk-LIVE-1&x=1", "sk-LIVE-1"), ("Cookie: sessionid=zzz", "zzz"),
])
def test_redaction(raw, secret):
    out = redact(raw)
    assert secret not in out and "********" in out


def test_log_files_created_and_redacted(client):
    logging.getLogger("scanner").info("gọi api access_token=SUPERSECRET")
    logging.getLogger("error").error("lỗi password=hunter2")
    logging.getLogger("scanner").error("scan lỗi refresh_token=ZZZ")
    for h in logging.getLogger("scanner").handlers:
        h.flush()
    for n in ("app", "api", "scanner", "error"):
        text = "\n".join(tail_log(settings.log_dir, n))
        assert "SUPERSECRET" not in text and "hunter2" not in text and "ZZZ" not in text
    assert any("access_token=********" in l for l in tail_log(settings.log_dir, "scanner"))
    assert client.get("/api/health").status_code == 200
    assert any("/api/health" in l for l in tail_log(settings.log_dir, "api"))
    assert client.get("/api/system/logs/passwd").status_code == 404   # chống đọc file tùy ý
    assert client.get("/api/system/logs/app").json()["lines"]


def test_unhandled_error_is_friendly(client):
    from app.main import app

    @app.get("/api/_boom")
    def boom():
        raise RuntimeError("Traceback secret internals")

    from fastapi.testclient import TestClient
    r = TestClient(app, raise_server_exceptions=False).get("/api/_boom")
    assert r.status_code == 500 and "Traceback" not in r.text and "RuntimeError" not in r.text
    assert "error.log" in r.json()["detail"]


# ---------- Ollama ----------
def test_ollama_not_running():
    def h(req):
        raise httpx.ConnectError("refused")
    with pytest.raises(AIProviderError) as e:
        mock_ollama(h).test_connection()
    assert e.value.code == "ollama_not_running" and "Ollama is not running" in e.value.user_message


def test_ollama_model_missing():
    h = lambda req: httpx.Response(200, json={"models": [{"name": "other:7b"}]})  # noqa: E731
    with pytest.raises(AIProviderError) as e:
        mock_ollama(h).test_connection()
    assert e.value.code == "model_missing" and "ollama pull llama3.2:3b" in e.value.user_message


def test_ollama_ok_and_timeout():
    def ok(req):
        if req.url.path == "/api/tags":
            return httpx.Response(200, json={"models": [{"name": "llama3.2:3b"}]})
        return httpx.Response(200, json={"response": "OK"})
    h = mock_ollama(ok).test_connection()
    assert h.ok and h.models_installed == ["llama3.2:3b"]

    def slow(req):
        raise httpx.ReadTimeout("slow")
    with pytest.raises(AIProviderError) as e:
        mock_ollama(slow).generate("hi")
    assert e.value.code == "timeout"


def test_ai_test_endpoint_when_ollama_offline(client):
    # không có Ollama thật trong môi trường test -> thông báo thân thiện, không lỗi 500
    r = client.post("/api/ai/test").json()
    assert r["ok"] is False and r["code"] in ("ollama_not_running", "network_error")
    assert "Ollama" in r["message"]
    usage = {u["service"]: u for u in client.get("/api/system/usage").json()}
    assert usage["ollama"]["errors"] == 1 and usage["ollama"]["requests_today"] == 1


# ---------- settings ----------
def test_general_settings_validation(client):
    g = client.get("/api/settings/general").json()
    assert g["ai_provider"] == "ollama" and g["ollama_model"] == "llama3.2:3b" and g["max_products_per_scan"] <= 100
    assert client.put("/api/settings/general", json={"ai_provider": "openai"}).status_code == 422  # trả phí: từ chối
    assert client.put("/api/settings/general", json={"max_products_per_scan": 99999}).status_code == 422
    assert client.put("/api/settings/general", json={"retry_count": -1}).status_code == 422
    assert client.put("/api/settings/general", json={"request_delay_seconds": "abc"}).status_code == 422
    assert client.put("/api/settings/general", json={"bogus": 1}).status_code == 422
    assert client.put("/api/settings/general", json={"ollama_model": "a b"}).status_code == 422
    r = client.put("/api/settings/general", json={"max_products_per_scan": 20, "retry_count": 5})
    assert r.json()["max_products_per_scan"] == 20 and client.get("/api/settings/general").json()["retry_count"] == 5


# ---------- demo/real separation ----------
def test_demo_never_mixes_with_real(client):
    client.post("/api/products/import", files={"file": ("a.csv", io.BytesIO(CSV.encode()), "text/csv")})
    client.put("/api/settings/general", json={"demo_mode": True})
    assert client.get("/api/products", params={"page_size": 100}).json()["total"] == 15        # chỉ DEMO
    r = client.post("/api/products/import", files={"file": ("a.csv", io.BytesIO(CSV.encode()), "text/csv")})
    assert r.status_code == 409                                                              # không nhập vào DEMO
    assert client.delete("/api/data").status_code == 409
    client.put("/api/settings/general", json={"demo_mode": False})
    items = client.get("/api/products").json()["items"]
    assert [i["name"] for i in items] == ["Thật"] and not items[0]["is_demo"]
    assert client.post("/api/demo/reset").json()["created"] == 15


# ---------- connections / cost / usage ----------
def test_connections_never_pretend(client):
    c = {x["marketplace"]: x for x in client.get("/api/connections").json()}
    assert set(c) == {"tiktok_shop", "shopee"}
    for x in c.values():
        assert x["status"] == "api_not_confirmed" and x["can_connect"] is False and x["availability"] == "NOT_CONFIRMED"
    assert "NOT CONFIRMED" in c["shopee"]["note"]
    r = client.post("/api/connections/shopee/connect")
    assert r.status_code == 501 and "không tạo dữ liệu giả" in r.json()["detail"]
    assert client.post("/api/connections/shopee/refresh").status_code == 409
    assert client.post("/api/connections/shopee/disconnect").status_code == 200
    assert client.post("/api/connections/lazada/connect").status_code == 404


def test_connectors_refuse_data(client):
    from app.services.marketplace import REGISTRY, NotAvailableError
    for conn in REGISTRY.values():
        for call in (conn.search_products, conn.get_affiliate_products):
            with pytest.raises(NotAvailableError):
                call()
        with pytest.raises(NotAvailableError):
            conn.get_commission("1")


def test_cost_monitor_is_honest(client):
    c = client.get("/api/system/cost").json()
    assert c["ai"]["cost_usd"] == 0.0 and c["cloud"]["cost_usd"] == 0.0
    assert all(m["cost"] == "Pricing not confirmed" for m in c["marketplace_api"])
    assert c["estimated_monthly_usd"] == 0.0 and c["any_marketplace_connected"] is False


def test_usage_has_unavailable_quota(client):
    u = client.get("/api/system/usage").json()
    assert {x["service"] for x in u} == {"tiktok_shop", "shopee", "ollama"}
    assert all(x["quota"] == "Quota information unavailable" and x["requests_today"] == 0 for x in u)
    assert client.get("/api/system/storage").json()["database"] == "SQLite"


# ---------- migration từ database bản Phase 1 cũ ----------
def test_upgrade_old_phase1_database(tmp_path):
    db = tmp_path / "old.db"
    con = sqlite3.connect(db)
    con.executescript("""
    CREATE TABLE products (id INTEGER PRIMARY KEY, platform VARCHAR(20) NOT NULL, external_id VARCHAR(120) NOT NULL,
      name VARCHAR(300) NOT NULL, url VARCHAR(1000), image_url VARCHAR(1000), category VARCHAR(120), price FLOAT,
      currency VARCHAR(3) NOT NULL DEFAULT 'VND', commission_rate FLOAT, rating FLOAT, review_count INTEGER,
      positive_review_pct FLOAT, negative_review_pct FLOAT, sold_count INTEGER, sold_30d INTEGER, sold_prev_30d INTEGER,
      competition VARCHAR(10), return_rate FLOAT, video_fit FLOAT, data_updated_at DATETIME,
      imported_at DATETIME NOT NULL, source VARCHAR(10) NOT NULL, source_label VARCHAR(200),
      is_favorite BOOLEAN NOT NULL DEFAULT 0, UNIQUE(platform, external_id));
    CREATE TABLE app_settings (key VARCHAR(60) PRIMARY KEY, value JSON NOT NULL, updated_at DATETIME NOT NULL);
    CREATE TABLE import_logs (id INTEGER PRIMARY KEY, filename VARCHAR(300) NOT NULL, created INTEGER NOT NULL,
      updated INTEGER NOT NULL, rejected INTEGER NOT NULL, errors TEXT, created_at DATETIME NOT NULL);
    INSERT INTO products (platform, external_id, name, imported_at, source) VALUES ('shopee','real-1','Của tôi','2025-01-01','csv');
    INSERT INTO products (platform, external_id, name, imported_at, source) VALUES ('shopee','demo-1','[DEMO] cũ','2025-01-01','demo');
    """)
    con.commit(); con.close()
    cfg = Config(str(BASE_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BASE_DIR / "migrations"))
    cfg.set_main_option("sqlalchemy.url", f"sqlite:///{db}")
    command.upgrade(cfg, "head")
    con = sqlite3.connect(db)
    names = [r[0] for r in con.execute("SELECT name FROM products")]
    cols = {r[1] for r in con.execute("PRAGMA table_info(products)")}
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert names == ["Của tôi"]                                   # dữ liệu thật giữ nguyên, DEMO cũ bị gỡ
    assert {"shop_name", "seller_rating", "commission_amount", "country", "created_at", "updated_at"} <= cols
    assert {"users", "marketplace_connections", "product_snapshots", "affiliate_links", "product_scores",
            "scan_jobs", "scan_results", "ai_analysis", "api_usage_logs"} <= tables
    assert con.execute("SELECT username FROM users").fetchall() == [("local",)]
    command.downgrade(cfg, "base")  # downgrade không lỗi
