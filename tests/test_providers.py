import httpx
import pytest

from app.config import Settings
from app.providers import (AnthropicProvider, MockProvider, OpenAIProvider, ToolCall,
                           get_provider)
from app.tools import TOOL_SPECS


def test_default_provider_is_mock():
    assert isinstance(get_provider(Settings()), MockProvider)


def test_provider_selection():
    assert isinstance(get_provider(Settings(llm_provider="openai", openai_api_key="k")), OpenAIProvider)
    assert isinstance(get_provider(Settings(llm_provider="Anthropic", anthropic_api_key="k")), AnthropicProvider)


def test_missing_keys_and_unknown_provider_fail_fast():
    with pytest.raises(ValueError):
        get_provider(Settings(llm_provider="openai"))
    with pytest.raises(ValueError):
        get_provider(Settings(llm_provider="anthropic"))
    with pytest.raises(ValueError):
        get_provider(Settings(llm_provider="llama"))


def test_settings_read_env(monkeypatch):
    from app.config import get_settings
    monkeypatch.setenv("LLM_PROVIDER", "OPENAI")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-x")
    s = get_settings()
    assert s.llm_provider == "openai" and s.openai_model == "gpt-x"


HISTORY = [
    {"role": "user", "content": "price of EL-1001?"},
    {"role": "assistant", "content": "", "tool_calls": [ToolCall("c1", "get_product", {"sku_or_name": "EL-1001"})]},
    {"role": "tool", "tool_call_id": "c1", "name": "get_product", "content": '{"found": true}'},
]


def test_openai_message_mapping():
    out = OpenAIProvider.to_payload_messages("sys", HISTORY)
    assert out[0] == {"role": "system", "content": "sys"}
    assert out[2]["tool_calls"][0]["function"]["name"] == "get_product"
    assert out[3] == {"role": "tool", "tool_call_id": "c1", "content": '{"found": true}'}


def test_anthropic_message_mapping():
    out = AnthropicProvider.to_payload_messages(HISTORY)
    assert out[1]["content"][0] == {"type": "tool_use", "id": "c1", "name": "get_product",
                                    "input": {"sku_or_name": "EL-1001"}}
    assert out[2]["role"] == "user" and out[2]["content"][0]["type"] == "tool_result"


def test_openai_parses_tool_calls(monkeypatch):
    def fake_post(url, json, timeout, headers):
        assert headers["Authorization"] == "Bearer k" and json["tools"][0]["type"] == "function"
        return httpx.Response(200, request=httpx.Request("POST", url), json={"choices": [{"message": {
            "content": None, "tool_calls": [{"id": "x", "type": "function", "function": {
                "name": "get_order_status", "arguments": '{"order_number": "ORD-1001"}'}}]}}]})
    monkeypatch.setattr(httpx, "post", fake_post)
    r = OpenAIProvider("k", "m").complete("s", [{"role": "user", "content": "hi"}], TOOL_SPECS)
    assert r.tool_calls[0].arguments == {"order_number": "ORD-1001"}


def test_anthropic_parses_text_and_tool_use(monkeypatch):
    def fake_post(url, json, timeout, headers):
        assert headers["x-api-key"] == "k" and "input_schema" in json["tools"][0]
        return httpx.Response(200, request=httpx.Request("POST", url), json={"content": [
            {"type": "text", "text": "Let me check."},
            {"type": "tool_use", "id": "t1", "name": "search_products", "input": {"query": "mouse"}}]})
    monkeypatch.setattr(httpx, "post", fake_post)
    r = AnthropicProvider("k", "m").complete("s", [{"role": "user", "content": "mouse?"}], TOOL_SPECS)
    assert r.text == "Let me check." and r.tool_calls[0].name == "search_products"


def test_mock_is_deterministic(provider):
    msgs = [{"role": "user", "content": "recommend a keyboard"}]
    a, b = provider.complete("", msgs, TOOL_SPECS), provider.complete("", msgs, TOOL_SPECS)
    assert a == b and a.tool_calls[0].name == "search_products"
