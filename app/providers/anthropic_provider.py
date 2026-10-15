import httpx

from .base import LLMResponse, ToolCall


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.anthropic.com/v1", timeout: float = 30):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is required for the anthropic provider")
        self.api_key, self.model, self.base_url, self.timeout = api_key, model, base_url, timeout

    @staticmethod
    def to_payload_messages(messages: list[dict]) -> list[dict]:
        out: list[dict] = []
        for m in messages:
            if m["role"] == "tool":
                block = {"type": "tool_result", "tool_use_id": m["tool_call_id"], "content": m["content"]}
                if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list):
                    out[-1]["content"].append(block)
                else:
                    out.append({"role": "user", "content": [block]})
            elif m["role"] == "assistant" and m.get("tool_calls"):
                blocks = [{"type": "text", "text": m["content"]}] if m.get("content") else []
                blocks += [{"type": "tool_use", "id": c.id, "name": c.name, "input": c.arguments}
                           for c in m["tool_calls"]]
                out.append({"role": "assistant", "content": blocks})
            else:
                out.append({"role": m["role"], "content": m["content"]})
        return out

    def complete(self, system, messages, tools):
        payload = {
            "model": self.model,
            "max_tokens": 800,
            "system": system,
            "messages": self.to_payload_messages(messages),
            "tools": [{"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
                      for t in tools],
        }
        r = httpx.post(f"{self.base_url}/messages", json=payload, timeout=self.timeout, headers={
            "x-api-key": self.api_key, "anthropic-version": "2023-06-01"})
        r.raise_for_status()
        text, calls = [], []
        for block in r.json().get("content", []):
            if block["type"] == "text":
                text.append(block["text"])
            elif block["type"] == "tool_use":
                calls.append(ToolCall(block["id"], block["name"], block.get("input") or {}))
        return LLMResponse(text="".join(text), tool_calls=calls)
