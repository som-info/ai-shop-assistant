from app.chat import ChatService


def test_recommendation_flow(session, provider):
    out = ChatService(session, provider).reply("I need headphones for travel")
    assert out["tools_used"] == ["search_products"]
    assert out["products"][0]["sku"] == "EL-1001"
    assert "AuraBeat" in out["reply"] and out["direction"] == "ltr"


def test_price_filter(session, provider):
    out = ChatService(session, provider).reply("gift under $40")
    assert out["products"] and all(p["price"] <= 40 for p in out["products"])


def test_price_and_stock_question(session, provider):
    out = ChatService(session, provider).reply("How much is the air fryer?")
    assert out["tools_used"] == ["get_product"]
    assert "$99.00" in out["reply"] and "out of stock" in out["reply"]


def test_order_lookup_and_follow_up(session, provider):
    svc = ChatService(session, provider)
    first = svc.reply("Where is my order?")
    assert first["tools_used"] == [] and "order number" in first["reply"]
    second = svc.reply("ORD-1002", first["session_id"])
    assert second["session_id"] == first["session_id"]
    assert "shipped" in second["reply"] and second["order"]["carrier"] == "UPS"


def test_unknown_order(session, provider):
    out = ChatService(session, provider).reply("status of ORD-4242")
    assert "couldn't find order ORD-4242" in out["reply"]


def test_history_is_persisted_per_session(client):
    a = client.post("/api/chat", json={"message": "hello"}).json()
    client.post("/api/chat", json={"message": "keyboard for programming", "session_id": a["session_id"]})
    b = client.post("/api/chat", json={"message": "hello"}).json()
    assert a["session_id"] != b["session_id"]
    hist = client.get(f"/api/sessions/{a['session_id']}").json()["messages"]
    assert [m["role"] for m in hist] == ["user", "assistant", "user", "assistant"]
    assert client.get("/api/sessions/nope").status_code == 404


def test_api_validation_and_health(client):
    assert client.get("/health").json() == {"status": "ok", "provider": "mock"}
    assert client.post("/api/chat", json={"message": ""}).status_code == 422
    assert len(client.get("/api/products").json()) == 20


def test_admin_stats_and_page(client):
    for q in ["Track ORD-1001", "track ord-1001", "سلام"]:
        client.post("/api/chat", json={"message": q})
    stats = client.get("/api/admin/stats").json()
    assert stats["top_questions"][0] == {"question": "track ord-1001", "count": 2}
    assert stats["tool_usage"]["get_order_status"] == 2
    assert stats["languages"] == {"en": 2, "fa": 1}
    page = client.get("/admin")
    assert page.status_code == 200 and "Top asked questions" in page.text


def test_admin_token(monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import Settings
    from app.main import create_app
    app = create_app(Settings(database_url="sqlite://", admin_token="secret"))
    with TestClient(app) as c:
        assert c.get("/admin").status_code == 401
        assert c.get("/admin?token=secret").status_code == 200
        assert c.get("/api/admin/stats", headers={"X-Admin-Token": "secret"}).status_code == 200


def test_store_page_embeds_widget(client):
    html = client.get("/").text
    assert "/static/widget.js" in html
    assert client.get("/static/widget.js").status_code == 200
