from app.chat import ChatService
from app.i18n import detect_language, normalize_fa, t, to_fa_digits


def test_detect_language():
    assert detect_language("Do you have headphones?") == "en"
    assert detect_language("هدفون دارید؟") == "fa"
    assert detect_language("قیمت EL-1001 چنده؟") == "fa"
    assert detect_language("1234") == "en"


def test_digit_and_letter_normalization():
    assert to_fa_digits(129) == "۱۲۹"
    assert normalize_fa("سفارش ۱۰۰۲ كي") == "سفارش 1002 کی"


def test_persian_template_uses_persian_digits():
    assert "۵۹" in t("fa", "price_line", name="x", price=59.0, stock="y")


def test_persian_recommendation_is_rtl(session, provider):
    out = ChatService(session, provider).reply("یک هدفون برای سفر پیشنهاد بده")
    assert out["language"] == "fa" and out["direction"] == "rtl"
    assert out["products"][0]["sku"] == "EL-1001"
    assert "پیشنهاد" in out["reply"] and "هدفون بی‌سیم AuraBeat" in out["reply"]


def test_persian_order_status(session, provider):
    out = ChatService(session, provider).reply("وضعیت سفارش ORD-۱۰۰۵ چیه؟")
    assert out["order"]["status"] == "out_for_delivery"
    assert "در مسیر تحویل" in out["reply"]


def test_persian_greeting(session, provider):
    out = ChatService(session, provider).reply("سلام")
    assert out["reply"].startswith("سلام!") and out["tools_used"] == []
