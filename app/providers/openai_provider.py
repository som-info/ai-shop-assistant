import json

import httpx

from .base import LLMResponse, ToolCall


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str, base_url: str = "https://api.openai.com/v1", timeout: float = 30):
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required for the openai provider")
        self.api_key, self.model, self.base_url, self.timeout = api_key, model, base_url, timeout

    @staticmethod
    def to_payload_messages(system: str, messages: list[dict]) -> list[dict]:
        out = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "tool":
                out.append({"role": "tool", "tool_call_id": m["tool_call_id"], "content": m["content"]})
            elif m["role"] == "assistant" and m.get("tool_calls"):
                out.append({"role": "assistant", "content": m.get("content") or None, "tool_calls": [
                    {"id": c.id, "type": "function",
                     "function": {"name": c.name, "arguments": json.dumps(c.arguments)}}
                    for c in m["tool_calls"]]})
            else:
                out.append({"role": m["role"], "content": m["content"]})
        return out

    def complete(self, system, messages, tools):
        payload = {
            "model": self.model,
            "messages": self.to_payload_messages(system, messages),
            "tools": [{"type": "function", "function": t} for t in tools],
            "temperature": 0.3,
        }
        r = httpx.post(f"{self.base_url}/chat/completions", json=payload, timeout=self.timeout,
                       headers={"Authorization": f"Bearer {self.api_key}"})
        r.raise_for_status()
        msg = r.json()["choices"][0]["message"]
        calls = [ToolCall(c["id"], c["function"]["name"], json.loads(c["function"].get("arguments") or "{}"))
                 for c in msg.get("tool_calls") or []]
        return LLMResponse(text=msg.get("content") or "", tool_calls=calls)
