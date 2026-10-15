import re
from collections import Counter
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from . import __version__
from .chat import ChatService
from .config import Settings, get_settings
from .db import Base, make_engine, make_session_factory
from .models import Conversation, Message, Product
from .providers import get_provider
from .seed import seed

HERE = Path(__file__).parent


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    session_id: str | None = Field(default=None, max_length=64)


def _normalize_question(text: str) -> str:
    text = re.sub(r"[?؟!.,]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    Base.metadata.create_all(engine)
    SessionLocal = make_session_factory(engine)
    with SessionLocal() as s:
        seed(s)
    provider = get_provider(settings)

    app = FastAPI(title="AI Shop Assistant", version=__version__)
    app.state.settings, app.state.provider = settings, provider
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
    app.mount("/static", StaticFiles(directory=HERE / "static"), name="static")
    templates = Jinja2Templates(directory=HERE / "templates")

    def db():
        with SessionLocal() as s:
            yield s

    def require_admin(token: str | None = Query(default=None), x_admin_token: str | None = Header(default=None)):
        if settings.admin_token and settings.admin_token not in (token, x_admin_token):
            raise HTTPException(401, "admin token required")

    @app.get("/health")
    def health():
        return {"status": "ok", "provider": provider.name}

    @app.get("/", response_class=HTMLResponse)
    def store(request: Request, session=Depends(db)):
        products = session.scalars(select(Product).order_by(Product.rating.desc()).limit(8)).all()
        return templates.TemplateResponse(request, "store.html",
                                          {"products": products, "store": settings.store_name})

    @app.get("/api/products")
    def products(category: str | None = None, session=Depends(db)):
        q = select(Product).order_by(Product.id)
        if category:
            q = q.where(Product.category == category)
        return [p.to_dict() for p in session.scalars(q)]

    @app.post("/api/chat")
    def chat(body: ChatIn, session=Depends(db)):
        svc = ChatService(session, provider, settings.store_name, settings.max_tool_rounds)
        try:
            return svc.reply(body.message, body.session_id)
        except Exception as exc:  # provider/network failure must not leak internals
            raise HTTPException(502, f"assistant unavailable: {type(exc).__name__}") from exc

    @app.get("/api/sessions/{session_id}")
    def history(session_id: str, session=Depends(db)):
        conv = session.scalar(select(Conversation).where(Conversation.session_id == session_id))
        if not conv:
            raise HTTPException(404, "session not found")
        return {"session_id": session_id, "language": conv.language,
                "messages": [{"role": m.role, "content": m.content} for m in conv.messages]}

    # --- admin -----------------------------------------------------------------
    def stats(session) -> dict:
        convs = session.scalars(select(Conversation).order_by(Conversation.updated_at.desc())).all()
        questions = session.scalars(select(Message.content).where(Message.role == "user")).all()
        top = Counter(_normalize_question(q) for q in questions).most_common(10)
        tool_counts = Counter()
        for tools in session.scalars(select(Message.tools_used).where(Message.role == "assistant")):
            tool_counts.update(t for t in (tools or "").split(",") if t)
        langs = Counter(c.language for c in convs)
        return {
            "conversations": [{
                "session_id": c.session_id, "language": c.language,
                "messages": len(c.messages), "updated_at": c.updated_at.isoformat(timespec="minutes"),
                "first_question": next((m.content for m in c.messages if m.role == "user"), ""),
                "transcript": [{"role": m.role, "content": m.content} for m in c.messages],
            } for c in convs],
            "top_questions": [{"question": q, "count": n} for q, n in top],
            "tool_usage": dict(tool_counts),
            "languages": dict(langs),
            "total_messages": session.scalar(select(func.count(Message.id))),
        }

    @app.get("/api/admin/stats", dependencies=[Depends(require_admin)])
    def admin_stats(session=Depends(db)):
        return stats(session)

    @app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
    def admin(request: Request, session=Depends(db)):
        return templates.TemplateResponse(request, "admin.html",
                                          {"s": stats(session), "store": settings.store_name,
                                           "provider": provider.name})

    return app

