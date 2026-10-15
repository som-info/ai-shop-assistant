from app.tools import StoreTools, normalize_order_number


def test_seeded_catalog_size(session):
    tools = StoreTools(session)
    assert len(tools._by_sku) == 20


def test_search_finds_relevant_products(session):
    res = StoreTools(session).search_products("noise cancelling headphones for travel")
    assert res["results"][0]["sku"] == "EL-1001"


def test_search_respects_price_and_stock_filters(session):
    tools = StoreTools(session)
    res = tools.search_products("gift", max_price=30, limit=5)
    assert res["results"] and all(p["price"] <= 30 for p in res["results"])
    res = tools.search_products("waterproof speaker", in_stock_only=True)
    assert all(p["sku"] != "EL-1003" for p in res["results"])


def test_persian_query_hits_english_catalog(session):
    res = StoreTools(session).search_products("اسپرسوساز برای قهوه")
    assert res["results"][0]["sku"] == "HM-2001"


def test_get_product_by_sku_and_name(session):
    tools = StoreTools(session)
    assert tools.get_product("el-1005")["product"]["name"] == "SwiftType Mechanical Keyboard"
    p = tools.get_product("air fryer")["product"]
    assert p["sku"] == "HM-2005" and p["in_stock"] is False


def test_order_status(session):
    tools = StoreTools(session)
    res = tools.get_order_status("ord 1002")
    assert res["found"] and res["status"] == "shipped" and res["carrier"] == "UPS"
    assert "SwiftType Mechanical Keyboard" in res["items"]
    assert tools.get_order_status("ORD-9999") == {"found": False, "order_number": "ORD-9999"}


def test_order_number_normalization():
    assert normalize_order_number("where is ord-1003?") == "ORD-1003"
    assert normalize_order_number("سفارش ORD-۱۰۰۵") == "ORD-1005"
    assert normalize_order_number("no number") is None


def test_dispatch_handles_bad_input(session):
    tools = StoreTools(session)
    assert "error" in tools.call("drop_tables", {})
    assert "error" in tools.call("get_product", "{not json")
    assert "error" in tools.call("get_product", {"unknown": 1})
    assert tools.call("get_product", '{"sku_or_name": "EL-1001"}')["found"]
