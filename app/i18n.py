"""Language detection, Persian helpers and UI/answer strings."""
import re

_FA_CHARS = re.compile(r"[\u0600-\u06FF]")
_FA_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_EN_TO_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")

# Small bilingual glossary so Persian questions can hit the English catalog index.
FA_GLOSSARY = {
    "هدفون": "headphones", "هدست": "headphones", "ایرباد": "earbuds", "هندزفری": "earbuds",
    "اسپیکر": "speaker", "بلندگو": "speaker", "موسیقی": "music", "آهنگ": "music",
    "وبکم": "webcam", "وب‌کم": "webcam", "دوربین": "camera", "کیبورد": "keyboard",
    "صفحه‌کلید": "keyboard", "ماوس": "mouse", "موس": "mouse", "شارژر": "charger",
    "پاوربانک": "powerbank", "ساعت": "smartwatch", "هوشمند": "smart", "دستبند": "band",
    "قهوه": "coffee", "اسپرسو": "espresso", "اسپرسوساز": "espresso", "آشپزخانه": "kitchen",
    "آشپزی": "cooking", "چاقو": "knife", "سرخ‌کن": "fryer", "هوا": "air", "تصفیه": "purifier",
    "لامپ": "bulb", "نور": "light", "خانه": "home", "کفش": "shoes", "دویدن": "running",
    "دو": "running", "رانینگ": "running", "ورزش": "sport", "ورزشی": "sport", "باشگاه": "gym",
    "یوگا": "yoga", "بطری": "bottle", "آب": "water", "کتاب": "book", "برنامه‌نویسی": "programming",
    "برنامه": "programming", "هدیه": "gift", "کادو": "gift", "سفر": "travel", "مسافرت": "travel",
    "کمپینگ": "camping", "کوه": "hiking", "بازی": "gaming", "گیمینگ": "gaming", "کار": "work",
    "اداری": "office", "سلامتی": "health", "خواب": "sleep", "ارزان": "budget", "لپ‌تاپ": "laptop",
    "گوشی": "phone", "موبایل": "phone", "بی‌سیم": "wireless", "نویز": "noise-cancelling",
}

STATUS_LABELS = {
    "en": {"processing": "being processed", "shipped": "shipped", "out_for_delivery": "out for delivery",
           "delivered": "delivered", "cancelled": "cancelled"},
    "fa": {"processing": "در حال پردازش", "shipped": "ارسال شده", "out_for_delivery": "در مسیر تحویل",
           "delivered": "تحویل داده شده", "cancelled": "لغو شده"},
}

STRINGS = {
    "en": {
        "greeting": "Hi! I'm the {store} shopping assistant. Ask me for product ideas, prices, stock or your order status.",
        "recommend_intro": "Here are some products I'd recommend:",
        "no_results": "I couldn't find a matching product. Try another keyword, e.g. \"headphones\" or \"coffee\".",
        "price_line": "{name} costs ${price:.2f} and is {stock}.",
        "in_stock": "in stock ({n} left)",
        "low_stock": "almost sold out (only {n} left)",
        "out_of_stock": "currently out of stock",
        "order_line": "Order {number} is {status}.",
        "order_eta": "Estimated delivery: {eta}.",
        "order_carrier": "Carrier: {carrier}.",
        "order_items": "Items: {items}. Total: ${total:.2f}.",
        "order_missing": "I couldn't find order {number}. Please double-check the number (format ORD-1234).",
        "order_ask": "Sure! Please send me your order number (for example ORD-1002).",
        "fallback": "I can help with product recommendations, prices, stock and order tracking. What are you looking for?",
    },
    "fa": {
        "greeting": "سلام! من دستیار خرید {store} هستم. درباره محصولات، قیمت، موجودی یا وضعیت سفارش بپرسید.",
        "recommend_intro": "این محصولات را پیشنهاد می‌کنم:",
        "no_results": "محصول مناسبی پیدا نکردم. لطفاً با کلمه دیگری امتحان کنید، مثلاً «هدفون» یا «قهوه».",
        "price_line": "قیمت {name} {price} دلار است و {stock}.",
        "in_stock": "موجود است ({n} عدد)",
        "low_stock": "تقریباً تمام شده (فقط {n} عدد)",
        "out_of_stock": "در حال حاضر ناموجود است",
        "order_line": "سفارش {number} {status} است.",
        "order_eta": "تاریخ تقریبی تحویل: {eta}",
        "order_carrier": "شرکت حمل: {carrier}",
        "order_items": "اقلام: {items} — مبلغ کل: {total} دلار",
        "order_missing": "سفارش {number} پیدا نشد. لطفاً شماره را بررسی کنید (مثل ORD-1234).",
        "order_ask": "حتماً! لطفاً شماره سفارش خود را بفرستید (مثلاً ORD-1002).",
        "fallback": "می‌توانم در پیشنهاد محصول، قیمت، موجودی و پیگیری سفارش کمکتان کنم. دنبال چه هستید؟",
    },
}


def detect_language(text: str) -> str:
    """Return 'fa' when the text is mostly Persian/Arabic script, else 'en'."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "en"
    fa = sum(1 for c in letters if _FA_CHARS.match(c))
    return "fa" if fa / len(letters) >= 0.3 else "en"


def normalize_digits(text: str) -> str:
    return text.translate(_FA_DIGITS)


def to_fa_digits(value) -> str:
    return str(value).translate(_EN_TO_FA_DIGITS)


def normalize_fa(text: str) -> str:
    """Unify Arabic/Persian letter variants and digits."""
    return normalize_digits(text).replace("ي", "ی").replace("ك", "ک").replace("\u200c", "‌")


def t(lang: str, key: str, **kwargs) -> str:
    table = STRINGS.get(lang, STRINGS["en"])
    text = table.get(key, STRINGS["en"][key])
    if lang == "fa":
        kwargs = {k: to_fa_digits(f"{v:g}" if isinstance(v, float) else v) if k in ("n", "price", "total") else v
                  for k, v in kwargs.items()}
    return text.format(**kwargs)


def status_label(lang: str, status: str) -> str:
    return STATUS_LABELS.get(lang, STATUS_LABELS["en"]).get(status, status)


def system_prompt(store: str) -> str:
    return (
        f"You are the friendly shopping assistant of the online store '{store}'. "
        "Use the provided tools to search the catalog, check price/stock and look up orders; "
        "never invent products, prices or order details. Keep answers short and helpful. "
        "Always reply in the same language as the customer: Persian (Farsi) if they write in Persian, otherwise English."
    )
