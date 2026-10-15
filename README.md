# AI Shop Assistant

A bilingual (English / Persian) shopping assistant chatbot for online stores.
A FastAPI backend runs an LLM with **tool / function calling** against the store's
catalog and order database, and a lightweight, dependency-free chat widget can be
embedded in any store page with a single `<script>` tag.

## Features

- **Product catalog** in SQLite via SQLAlchemy 2.0, seeded with 20 sample products and 5 orders.
- **Chat endpoint** (`POST /api/chat`) that answers questions, recommends products,
  checks price / stock and looks up order status by order number (`ORD-1002`).
- **Function calling**: the model can call `search_products`, `get_product` and `get_order_status`;
  the backend executes them and feeds results back (multi-round loop, capped by `MAX_TOOL_ROUNDS`).
- **Pluggable providers**: `openai` (Chat Completions tools), `anthropic` (Messages API `tool_use`)
  and a deterministic offline `mock` provider used by default and in tests — the demo runs without any API key.
- **Retrieval**: tiny pure-Python TF-IDF index over product names, tags and descriptions,
  with a small Persian→English glossary so Persian questions match the catalog.
- **English & Persian replies**, Persian digit normalization and full **RTL** rendering in the widget.
- **Per-session history** stored in the database and restored in the widget (localStorage session id).
- **Admin page** (`/admin`) with conversations, transcripts, top asked questions, language split and tool usage;
  optionally protected with `ADMIN_TOKEN`.
- Dockerfile + docker-compose, pytest suite, MIT license.

## Quick start

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env              # LLM_PROVIDER=mock by default
uvicorn app.main:create_app --factory --reload
```

Open <http://localhost:8000> (demo store with the widget) and <http://localhost:8000/admin>.

### Docker

```bash
docker compose up --build
```

### Using a real LLM

Set in `.env`:

```env
LLM_PROVIDER=openai        # or anthropic
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4o-mini
```

## Embedding the widget

```html
<script src="https://assistant.example.com/static/widget.js"
        data-api="https://assistant.example.com"
        data-title="My Store Assistant" defer></script>
```

`window.ShopAssistant.open()`, `.close()` and `.send(text)` are available for custom triggers.

## API

| Method | Path | Description |
|---|---|---|
| POST | `/api/chat` | `{message, session_id?}` → `{reply, session_id, language, direction, tools_used, products, order}` |
| GET | `/api/sessions/{id}` | Conversation history |
| GET | `/api/products` | Catalog (`?category=`) |
| GET | `/api/admin/stats` | Conversations, top questions, tool usage |
| GET | `/admin` | Admin dashboard |
| GET | `/health` | Health check + active provider |

## Project layout

```
app/
  main.py            FastAPI app factory & routes
  chat.py            conversation loop (history, tool calls, persistence)
  tools.py           tool schemas + implementations
  retrieval.py       TF-IDF retriever
  i18n.py            language detection, Persian helpers, reply templates
  providers/         openai, anthropic, mock
  static/widget.js   embeddable chat widget
  templates/         demo store + admin page
tests/               pytest suite
```

## Tests

```bash
pytest
```

The suite covers the tools, provider selection and request/response mapping (HTTP mocked),
the full chat flow with the mock provider, session history, admin stats and Persian/RTL behaviour.

## License

MIT

---

## خلاصه فارسی

**دستیار خرید هوشمند** یک چت‌بات دوزبانه (فارسی/انگلیسی) برای فروشگاه‌های اینترنتی است.
بک‌اند با FastAPI نوشته شده و مدل زبانی با فراخوانی ابزار (Function Calling) محصولات را جستجو می‌کند،
قیمت و موجودی را اعلام می‌کند و وضعیت سفارش را با شماره سفارش پیگیری می‌کند.
ارائه‌دهنده مدل قابل تعویض است (OpenAI، Anthropic یا حالت آفلاین Mock برای دمو و تست).
ویجت چت سبک با پشتیبانی کامل راست‌به‌چپ با یک تگ `script` در هر سایتی نصب می‌شود
و پنل مدیریت، گفتگوها و پرتکرارترین سؤال‌های مشتریان را نمایش می‌دهد.
