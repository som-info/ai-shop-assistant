/* Embeddable shopping assistant widget.
 * Usage: <script src="https://your-api/static/widget.js" data-api="https://your-api" defer></script>
 */
(function () {
  const script = document.currentScript;
  const API = (script && script.dataset.api) || window.location.origin;
  const TITLE = (script && script.dataset.title) || "Shopping Assistant";
  const OPEN = script && script.dataset.open === "true";
  const KEY = "shop-assistant-session";

  const css = `
  .sa-launcher{position:fixed;right:24px;bottom:24px;width:60px;height:60px;border-radius:50%;border:0;cursor:pointer;
    background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;box-shadow:0 10px 30px rgba(79,70,229,.45);font-size:26px;z-index:9998}
  .sa-panel{position:fixed;right:24px;bottom:96px;width:380px;max-width:calc(100vw - 32px);height:600px;max-height:calc(100vh - 120px);
    background:#fff;border-radius:18px;box-shadow:0 24px 60px rgba(15,23,42,.25);display:none;flex-direction:column;overflow:hidden;
    font-family:"Inter","Vazirmatn",system-ui,-apple-system,"Segoe UI",Tahoma,sans-serif;z-index:9999}
  .sa-panel.open{display:flex}
  .sa-head{background:linear-gradient(135deg,#4f46e5,#7c3aed);color:#fff;padding:16px 18px;display:flex;align-items:center;gap:12px}
  .sa-avatar{width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,.2);display:grid;place-items:center;font-size:20px}
  .sa-head h3{margin:0;font-size:15px;font-weight:600}.sa-head small{opacity:.85;font-size:12px}
  .sa-close{margin-left:auto;background:none;border:0;color:#fff;font-size:22px;cursor:pointer}
  .sa-body{flex:1;overflow-y:auto;padding:16px;background:#f8fafc;display:flex;flex-direction:column;gap:10px}
  .sa-msg{max-width:85%;padding:10px 14px;border-radius:14px;font-size:14px;line-height:1.55;white-space:pre-line;word-wrap:break-word}
  .sa-msg.user{align-self:flex-end;background:#4f46e5;color:#fff;border-bottom-right-radius:4px}
  .sa-msg.bot{align-self:flex-start;background:#fff;color:#0f172a;border:1px solid #e2e8f0;border-bottom-left-radius:4px}
  .sa-msg[dir=rtl]{text-align:right}
  .sa-msg.user[dir=rtl]{border-bottom-right-radius:14px;border-bottom-left-radius:4px}
  .sa-cards{display:flex;gap:8px;overflow-x:auto;padding-bottom:4px;align-self:stretch}
  .sa-card{min-width:140px;background:#fff;border:1px solid #e2e8f0;border-radius:12px;padding:10px;font-size:12px}
  .sa-card b{display:block;font-size:12.5px;color:#0f172a;margin-bottom:4px}
  .sa-price{color:#4f46e5;font-weight:700}.sa-out{color:#dc2626}.sa-in{color:#16a34a}
  .sa-order{align-self:stretch;background:#eef2ff;border:1px solid #c7d2fe;border-radius:12px;padding:10px 12px;font-size:12.5px}
  .sa-badge{display:inline-block;padding:2px 8px;border-radius:999px;background:#4f46e5;color:#fff;font-size:11px;text-transform:capitalize}
  .sa-chips{display:flex;flex-wrap:wrap;gap:6px;padding:8px 12px 0;background:#fff}
  .sa-chip{border:1px solid #c7d2fe;background:#eef2ff;color:#4338ca;border-radius:999px;padding:5px 10px;font-size:12px;cursor:pointer}
  .sa-form{display:flex;gap:8px;padding:12px;background:#fff;border-top:1px solid #e2e8f0}
  .sa-form input{flex:1;border:1px solid #cbd5e1;border-radius:12px;padding:10px 12px;font-size:14px;outline:none;font-family:inherit}
  .sa-form input:focus{border-color:#6366f1;box-shadow:0 0 0 3px rgba(99,102,241,.15)}
  .sa-form button{background:#4f46e5;color:#fff;border:0;border-radius:12px;padding:0 16px;cursor:pointer;font-weight:600}
  .sa-typing{align-self:flex-start;color:#64748b;font-size:12px}`;
  const style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  const launcher = el("button", "sa-launcher", "💬");
  launcher.setAttribute("aria-label", "Open chat");
  const panel = el("div", "sa-panel");
  panel.innerHTML = `
    <div class="sa-head"><div class="sa-avatar">🛍️</div>
      <div><h3>${escapeHtml(TITLE)}</h3><small>Online · English / فارسی</small></div>
      <button class="sa-close" aria-label="Close">×</button></div>
    <div class="sa-body" role="log" aria-live="polite"></div>
    <div class="sa-chips"></div>
    <form class="sa-form"><input name="q" autocomplete="off" placeholder="Ask about products or orders… / بپرسید…" />
      <button type="submit">Send</button></form>`;
  document.body.append(launcher, panel);

  const body = panel.querySelector(".sa-body");
  const form = panel.querySelector("form");
  const input = form.querySelector("input");
  const chips = panel.querySelector(".sa-chips");
  ["Headphones for travel", "Gift under $50", "Track ORD-1002", "قهوه‌ساز پیشنهاد بده"].forEach((c) => {
    const b = el("button", "sa-chip", c);
    b.type = "button";
    b.onclick = () => send(c);
    chips.appendChild(b);
  });

  const toggle = (open) => panel.classList.toggle("open", open);
  launcher.onclick = () => toggle(!panel.classList.contains("open"));
  panel.querySelector(".sa-close").onclick = () => toggle(false);
  form.onsubmit = (e) => { e.preventDefault(); send(input.value); };

  bubble("bot", "Hi! 👋 Ask me for product ideas, prices, stock or your order status.\nسلام! به فارسی هم می‌توانید بپرسید.");
  restore();
  if (OPEN) toggle(true);

  function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text) e.textContent = text; return e; }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
  function isRtl(text) { return /[\u0600-\u06FF]/.test(text) && (text.match(/[\u0600-\u06FF]/g) || []).length / text.replace(/\s/g, "").length > 0.3; }
  function scroll() { body.scrollTop = body.scrollHeight; }

  function bubble(role, text, dir) {
    const b = el("div", "sa-msg " + role, text);
    b.dir = dir || (isRtl(text) ? "rtl" : "ltr");
    body.appendChild(b); scroll(); return b;
  }

  function cards(products, dir) {
    if (!products || !products.length) return;
    const wrap = el("div", "sa-cards"); wrap.dir = dir;
    products.forEach((p) => {
      const c = el("div", "sa-card");
      const name = dir === "rtl" && p.name_fa ? p.name_fa : p.name;
      const stock = p.in_stock ? `<span class="sa-in">● ${dir === "rtl" ? "موجود" : "In stock"}</span>` : `<span class="sa-out">● ${dir === "rtl" ? "ناموجود" : "Out of stock"}</span>`;
      c.innerHTML = `<b>${escapeHtml(name)}</b><span class="sa-price">$${p.price.toFixed(2)}</span> · ★ ${p.rating}<br>${stock}`;
      wrap.appendChild(c);
    });
    body.appendChild(wrap); scroll();
  }

  function orderCard(o, dir) {
    if (!o || !o.found) return;
    const c = el("div", "sa-order"); c.dir = dir;
    c.innerHTML = `<b>${escapeHtml(o.order_number)}</b> &nbsp;<span class="sa-badge">${escapeHtml(o.status.replace(/_/g, " "))}</span>` +
      (o.eta ? `<br>ETA: ${escapeHtml(o.eta)}` : "") + (o.carrier ? ` · ${escapeHtml(o.carrier)}` : "");
    body.appendChild(c); scroll();
  }

  async function restore() {
    const sid = localStorage.getItem(KEY);
    if (!sid) return;
    try {
      const r = await fetch(`${API}/api/sessions/${encodeURIComponent(sid)}`);
      if (!r.ok) return;
      (await r.json()).messages.forEach((m) => bubble(m.role === "user" ? "user" : "bot", m.content));
    } catch (_) { /* offline: start fresh */ }
  }

  async function send(text) {
    text = (text || "").trim();
    if (!text) return;
    input.value = "";
    bubble("user", text);
    const typing = el("div", "sa-typing", "…");
    body.appendChild(typing); scroll();
    try {
      const r = await fetch(`${API}/api/chat`, {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({message: text, session_id: localStorage.getItem(KEY)}),
      });
      const data = await r.json();
      typing.remove();
      if (!r.ok) throw new Error(data.detail || r.status);
      localStorage.setItem(KEY, data.session_id);
      bubble("bot", data.reply, data.direction);
      cards(data.products, data.direction);
      orderCard(data.order, data.direction);
    } catch (e) {
      typing.remove();
      bubble("bot", "Sorry, something went wrong. Please try again.");
    }
  }

  window.ShopAssistant = { open: () => toggle(true), close: () => toggle(false), send };
})();
