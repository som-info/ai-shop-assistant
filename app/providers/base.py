from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)


class LLMProvider(Protocol):
    name: str

    def complete(self, system: str, messages: list[dict], tools: list[dict]) -> LLMResponse:
        """messages use a neutral format:
        {"role": "user"|"assistant", "content": str, "tool_calls": [ToolCall]?}
        {"role": "tool", "tool_call_id": str, "name": str, "content": str(json)}
        """
        ...
