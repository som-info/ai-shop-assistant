from ..config import Settings
from .anthropic_provider import AnthropicProvider
from .base import LLMProvider, LLMResponse, ToolCall
from .mock_provider import MockProvider
from .openai_provider import OpenAIProvider

__all__ = ["get_provider", "LLMProvider", "LLMResponse", "ToolCall",
           "MockProvider", "OpenAIProvider", "AnthropicProvider"]


def get_provider(settings: Settings) -> LLMProvider:
    name = (settings.llm_provider or "mock").lower()
    if name == "openai":
        return OpenAIProvider(settings.openai_api_key, settings.openai_model)
    if name == "anthropic":
        return AnthropicProvider(settings.anthropic_api_key, settings.anthropic_model)
    if name == "mock":
        return MockProvider(settings.store_name)
    raise ValueError(f"Unknown LLM_PROVIDER '{settings.llm_provider}' (use mock, openai or anthropic)")
