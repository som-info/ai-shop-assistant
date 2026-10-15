"""Deterministic, offline provider.

It imitates an LLM that uses function calling: on a fresh user turn it decides
which tool to call (rule based), and once tool results are available it writes
a templated answer in the customer's language. Used by default and in tests.
"""
import json
import re

from ..i18n import detect_language, normalize_digits, status_label, t
from ..tools import normalize_order_number
from .base import LLMResponse, ToolCall

ORDER_WORDS = ("order", "track", "tracking", "delivery", "shipment", "سفارش", "پیگیری", "مرسوله", "ارسال")
PRICE_WORDS = ("price", "cost", "how much", "stock", "available", "availability", "in stock",
               "قیمت", "چند", "موجود", "موجودی", "هزینه")
GREETINGS = ("hi", "hello", "hey", "salam", "سلام", "درود")
PRICE_LIMIT = re.compile(r"(?:under|below|less than|max|up to|زیر|کمتر از|تا)\s*\$?\s*(\d+(?:\.\d+)?)", re.I)
_STRIP = re.compile(r"\b(what'?s|what is|the|price|cost|of|how much|is|are|in stock|stock|available|does|do|you|have)\b|[?؟!.,$]",
                    re.I)


class MockProvider:
    name = "mock"

    def __init__(self, store_name: str = "Nova Store"):
        self.store_name = store_name

    def complete(self, system, messages, tools):
        last_user_idx = max(i for i, m in enumerate(messages) if m["role"] == "user")
        user_text = messages[last_user_idx]["content"]
        lang = detect_language(user_text)
        tool_msgs = [m for m in messages[last_user_idx + 1:] if m["role"] == "tool"]
        if tool_msgs:
            return LLMResponse(text=self._compose(lang, tool_msgs))
        return self._plan(user_text, lang, last_user_idx)

    # --- step 1: decide tool ---------------------------------------------------
    def _plan(self, text: str, lang: str, turn: int) -> LLMResponse:
        norm = normalize_digits(text).strip()
        low = norm.lower()
        call_id = f"call_{turn}"
        number = normalize_order_number(norm)
        if number:
            return LLMResponse(tool_calls=[ToolCall(call_id, "get_order_status", {"order_number": number})])
        if any(w in low for w in ORDER_WORDS):
            return LLMResponse(text=t(lang, "order_ask"))
        words = re.findall(r"\w+", low)
        if words and all(w in GREETINGS for w in words):
            return LLMResponse(text=t(lang, "greeting", store=self.store_name))
        if any(w in low for w in PRICE_WORDS) and not PRICE_LIMIT.search(low):
            name = _STRIP.sub(" ", norm)
            for w in PRICE_WORDS:
                name = name.replace(w, " ")
            name = re.sub(r"\s+", " ", name).strip() or norm
            return LLMResponse(tool_calls=[ToolCall(call_id, "get_product", {"sku_or_name": name})])
        args: dict = {"query": norm, "limit": 3}
        m = PRICE_LIMIT.search(low)
        if m:
            args["max_price"] = float(m.group(1))
            args["query"] = PRICE_LIMIT.sub(" ", norm)
        return LLMResponse(tool_calls=[ToolCall(call_id, "search_products", args)])

    # --- step 2: write answer --------------------------------------------------
    def _compose(self, lang: str, tool_msgs: list[dict]) -> str:
        parts = []
        for m in tool_msgs:
            data = json.loads(m["content"])
            name = m.get("name")
            if name == "search_products":
                parts.append(self._recommend(lang, data.get("results", [])))
            elif name == "get_product":
                if data.get("found"):
                    parts.append(self._price(lang, data["product"]))
                else:
                    parts.append(t(lang, "no_results"))
            elif name == "get_order_status":
                parts.append(self._order(lang, data))
        return "\n\n".join(p for p in parts if p) or t(lang, "fallback")

    def _display_name(self, lang, p):
        return p.get("name_fa") or p["name"] if lang == "fa" else p["name"]

    def _stock(self, lang, n):
        if n <= 0:
            return t(lang, "out_of_stock")
        if n <= 5:
            return t(lang, "low_stock", n=n)
        return t(lang, "in_stock", n=n)

    def _recommend(self, lang, results):
        if not results:
            return t(lang, "no_results")
        lines = [t(lang, "recommend_intro")]
        for p in results:
            price = t(lang, "price_line", name=self._display_name(lang, p), price=p["price"],
                      stock=self._stock(lang, p["stock"]))
            lines.append(f"• {price}")
        return "\n".join(lines)

    def _price(self, lang, p):
        return t(lang, "price_line", name=self._display_name(lang, p), price=p["price"],
                 stock=self._stock(lang, p["stock"]))

    def _order(self, lang, data):
        if not data.get("found"):
            return t(lang, "order_missing", number=data.get("order_number", "?"))
        lines = [t(lang, "order_line", number=data["order_number"], status=status_label(lang, data["status"]))]
        if data.get("carrier"):
            lines.append(t(lang, "order_carrier", carrier=data["carrier"]))
        if data.get("eta") and data["status"] not in ("delivered", "cancelled"):
            lines.append(t(lang, "order_eta", eta=data["eta"]))
        lines.append(t(lang, "order_items", items=", ".join(data["items"]), total=data["total"]))
        return "\n".join(lines)
