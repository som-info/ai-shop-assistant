"""Store tools exposed to the LLM via function calling."""
import json
import re

from sqlalchemy import func, select

from .i18n import normalize_digits
from .models import Order, Product
from .retrieval import TfidfIndex, product_document

ORDER_RE = re.compile(r"\bORD[-\s]?(\d{3,8})\b", re.IGNORECASE)

TOOL_SPECS = [
    {
        "name": "search_products",
        "description": "Search the store catalog by free text (needs, use case, product type). Returns best matches with price and stock.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "What the customer is looking for, in English keywords if possible."},
                "max_price": {"type": "number", "description": "Optional maximum price in USD."},
                "in_stock_only": {"type": "boolean", "description": "Only return products that are in stock."},
                "limit": {"type": "integer", "description": "Max results (1-5).", "default": 3},
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_product",
        "description": "Get price, stock and details of one product by SKU or (partial) name.",
        "parameters": {
            "type": "object",
            "properties": {"sku_or_name": {"type": "string"}},
            "required": ["sku_or_name"],
        },
    },
    {
        "name": "get_order_status",
        "description": "Look up an order by its number (format ORD-1234) and return status, items, carrier and ETA.",
        "parameters": {
            "type": "object",
            "properties": {"order_number": {"type": "string"}},
            "required": ["order_number"],
        },
    },
]


def normalize_order_number(raw: str) -> str | None:
    m = ORDER_RE.search(normalize_digits(raw or ""))
    return f"ORD-{m.group(1)}" if m else None


class StoreTools:
    def __init__(self, session):
        self.session = session
        products = session.scalars(select(Product)).all()
        self._by_sku = {p.sku: p for p in products}
        self.index = TfidfIndex({p.sku: product_document(p) for p in products})

    # --- tools -------------------------------------------------------------
    def search_products(self, query: str, max_price: float | None = None,
                        in_stock_only: bool = False, limit: int = 3) -> dict:
        limit = max(1, min(int(limit or 3), 5))
        hits = self.index.search(query, k=20)
        results = []
        for sku, score in hits:
            p = self._by_sku[sku]
            if max_price is not None and p.price > float(max_price):
                continue
            if in_stock_only and p.stock <= 0:
                continue
            results.append({**p.to_dict(), "score": round(score, 3)})
            if len(results) >= limit:
                break
        return {"query": query, "results": results}

    def get_product(self, sku_or_name: str) -> dict:
        key = (sku_or_name or "").strip()
        p = self._by_sku.get(key.upper())
        if p is None:
            p = self.session.scalar(
                select(Product).where(func.lower(Product.name).contains(key.lower())).limit(1)
            ) or self.session.scalar(select(Product).where(Product.name_fa.contains(key)).limit(1))
        if p is None:
            hits = self.index.search(key, k=1)
            p = self._by_sku[hits[0][0]] if hits else None
        if p is None:
            return {"found": False, "query": sku_or_name}
        return {"found": True, "product": p.to_dict()}

    def get_order_status(self, order_number: str) -> dict:
        number = normalize_order_number(order_number) or (order_number or "").strip().upper()
        o = self.session.scalar(select(Order).where(Order.number == number))
        if o is None:
            return {"found": False, "order_number": number}
        items = [self._by_sku[s].name if s in self._by_sku else s for s in o.items.split(",") if s]
        return {"found": True, "order_number": o.number, "status": o.status, "items": items,
                "total": o.total, "carrier": o.carrier, "eta": o.eta}

    # --- dispatch ------------------------------------------------------------
    def call(self, name: str, arguments: dict | str) -> dict:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments or "{}")
            except json.JSONDecodeError:
                return {"error": "invalid JSON arguments"}
        fn = {"search_products": self.search_products, "get_product": self.get_product,
              "get_order_status": self.get_order_status}.get(name)
        if fn is None:
            return {"error": f"unknown tool {name}"}
        try:
            return fn(**(arguments or {}))
        except TypeError as exc:
            return {"error": f"bad arguments: {exc}"}
