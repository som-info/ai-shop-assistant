import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv(path: str = ".env") -> None:
    """Minimal .env loader (no extra dependency). Existing env vars win."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


@dataclass
class Settings:
    llm_provider: str = "mock"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-latest"
    database_url: str = "sqlite:///./shop.db"
    store_name: str = "Nova Store"
    admin_token: str = ""
    max_tool_rounds: int = 4
    extra: dict = field(default_factory=dict)


def get_settings() -> Settings:
    _load_dotenv()
    env = os.environ
    return Settings(
        llm_provider=env.get("LLM_PROVIDER", "mock").lower(),
        openai_api_key=env.get("OPENAI_API_KEY", ""),
        openai_model=env.get("OPENAI_MODEL", "gpt-4o-mini"),
        anthropic_api_key=env.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=env.get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"),
        database_url=env.get("DATABASE_URL", "sqlite:///./shop.db"),
        store_name=env.get("STORE_NAME", "Nova Store"),
        admin_token=env.get("ADMIN_TOKEN", ""),
        max_tool_rounds=int(env.get("MAX_TOOL_ROUNDS", "4")),
    )
