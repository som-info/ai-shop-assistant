"""Chat orchestration: history, tool-calling loop and persistence."""
import json
import uuid

from sqlalchemy import select

from .i18n import detect_language, system_prompt, t
from .models import Conversation, Message
from .providers import LLMProvider
from .tools import TOOL_SPECS, StoreTools

HISTORY_TURNS = 10


class ChatService:
    def __init__(self, session, provider: LLMProvider, store_name: str = "Nova Store", max_rounds: int = 4):
        self.session = session
        self.provider = provider
        self.store_name = store_name
        self.max_rounds = max_rounds
        self.tools = StoreTools(session)

    def _conversation(self, session_id: str | None) -> Conversation:
        if session_id:
            conv = self.session.scalar(select(Conversation).where(Conversation.session_id == session_id))
            if conv:
                return conv
        conv = Conversation(session_id=session_id or uuid.uuid4().hex)
        self.session.add(conv)
        self.session.flush()
        return conv

    def reply(self, text: str, session_id: str | None = None) -> dict:
        text = (text or "").strip()[:2000]
        conv = self._conversation(session_id)
        lang = detect_language(text)
        conv.language = lang

        history = [{"role": m.role, "content": m.content} for m in conv.messages[-HISTORY_TURNS * 2:]]
        messages = history + [{"role": "user", "content": text}]
        used, products, order = [], [], None
        answer = ""
        for _ in range(self.max_rounds):
            resp = self.provider.complete(system_prompt(self.store_name), messages, TOOL_SPECS)
            if not resp.tool_calls:
                answer = resp.text
                break
            messages.append({"role": "assistant", "content": resp.text, "tool_calls": resp.tool_calls})
            for call in resp.tool_calls:
                result = self.tools.call(call.name, call.arguments)
                used.append(call.name)
                if call.name == "search_products":
                    products.extend(result.get("results", []))
                elif call.name == "get_product" and result.get("found"):
                    products.append(result["product"])
                elif call.name == "get_order_status":
                    order = result
                messages.append({"role": "tool", "tool_call_id": call.id, "name": call.name,
                                 "content": json.dumps(result, ensure_ascii=False)})
        if not answer:
            answer = t(lang, "fallback")

        self.session.add(Message(conversation_id=conv.id, role="user", content=text))
        self.session.add(Message(conversation_id=conv.id, role="assistant", content=answer,
                                 tools_used=",".join(dict.fromkeys(used))))
        self.session.commit()
        return {"session_id": conv.session_id, "reply": answer, "language": lang,
                "direction": "rtl" if lang == "fa" else "ltr", "tools_used": list(dict.fromkeys(used)),
                "products": products[:5], "order": order}
