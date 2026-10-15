"""Sample catalog and orders used by the demo and the tests."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from .models import Order, Product

PRODUCTS = [
    ("EL-1001", "AuraBeat Wireless Headphones", "هدفون بی‌سیم AuraBeat", "audio", "Over-ear Bluetooth headphones with active noise cancelling, 40-hour battery and soft memory-foam cushions. Great for travel, commuting and focus.", "headphones bluetooth noise-cancelling travel music", 129.0, 34, 4.6),
    ("EL-1002", "PulseBuds Pro Earbuds", "ایرباد PulseBuds Pro", "audio", "True wireless earbuds with ANC, transparency mode, IPX5 sweat resistance and a pocket charging case. Ideal for running and gym workouts.", "earbuds wireless sport running gym music", 89.0, 52, 4.4),
    ("EL-1003", "BoomCube Portable Speaker", "اسپیکر قابل حمل BoomCube", "audio", "Rugged waterproof Bluetooth speaker with 360-degree sound and 18-hour battery for parties, beach and camping.", "speaker bluetooth waterproof outdoor party camping", 59.0, 0, 4.3),
    ("EL-1004", "Lumen 4K Webcam", "وب‌کم ۴K لومن", "computers", "4K webcam with auto focus, dual noise-reducing microphones and privacy shutter for video calls and streaming.", "webcam camera video calls streaming work", 74.0, 18, 4.2),
    ("EL-1005", "SwiftType Mechanical Keyboard", "کیبورد مکانیکی SwiftType", "computers", "Compact 75% mechanical keyboard with hot-swappable switches, RGB backlight and USB-C. Loved by programmers and gamers.", "keyboard mechanical gaming programming rgb", 99.0, 25, 4.7),
    ("EL-1006", "GlideMouse Ergonomic Mouse", "ماوس ارگونومیک GlideMouse", "computers", "Vertical ergonomic wireless mouse that reduces wrist strain, with silent clicks and multi-device pairing.", "mouse ergonomic wireless office work", 45.0, 40, 4.5),
    ("EL-1007", "VoltCharge 65W GaN Charger", "شارژر ۶۵ وات VoltCharge", "accessories", "Tiny 65W GaN USB-C charger with three ports that powers a laptop, phone and earbuds at the same time. Perfect travel charger.", "charger usb-c laptop phone travel fast-charging", 39.0, 70, 4.6),
    ("EL-1008", "PowerVault 20000 Power Bank", "پاوربانک PowerVault", "accessories", "20000 mAh power bank with 22.5W fast charging, LED display and two USB outputs for long trips and camping.", "powerbank battery travel camping phone", 35.0, 3, 4.4),
    ("EL-1009", "Orbit Smartwatch S2", "ساعت هوشمند Orbit S2", "wearables", "Fitness smartwatch with heart-rate, sleep tracking, GPS, AMOLED screen and 7-day battery. Tracks running, cycling and swimming.", "smartwatch fitness running gps health sleep", 149.0, 12, 4.5),
    ("EL-1010", "FitBand Lite", "دستبند سلامتی FitBand Lite", "wearables", "Lightweight fitness band that counts steps, monitors heart rate and sleep, with a 14-day battery. Budget friendly gift.", "fitness band steps health budget gift", 29.0, 60, 4.1),
    ("HM-2001", "BrewMaster Espresso Machine", "اسپرسوساز BrewMaster", "kitchen", "15-bar espresso machine with milk frother for lattes and cappuccinos at home. Easy to clean, compact design.", "coffee espresso kitchen latte cappuccino", 219.0, 9, 4.6),
    ("HM-2002", "PureMist Air Purifier", "دستگاه تصفیه هوا PureMist", "home", "HEPA air purifier for rooms up to 40 m2, removes dust, pollen and smoke. Quiet sleep mode for bedrooms.", "air purifier hepa allergy bedroom home", 159.0, 14, 4.4),
    ("HM-2003", "SmartGlow LED Bulb (4-pack)", "لامپ هوشمند SmartGlow", "home", "Wi-Fi colour LED bulbs controllable by app or voice assistant, with schedules and 16 million colours.", "smart home light bulb led wifi", 32.0, 80, 4.3),
    ("HM-2004", "ChefPro Knife Set", "سرویس چاقوی ChefPro", "kitchen", "Five-piece stainless steel kitchen knife set with wooden block. Sharp, balanced and dishwasher safe.", "knife kitchen cooking chef gift", 69.0, 22, 4.5),
    ("HM-2005", "AirCrisp Air Fryer 5L", "سرخ‌کن بدون روغن AirCrisp", "kitchen", "5-litre air fryer for healthy oil-free cooking with 8 presets and a digital touch panel.", "air fryer kitchen healthy cooking", 99.0, 0, 4.6),
    ("SP-3001", "TrailRunner Running Shoes", "کفش رانینگ TrailRunner", "sports", "Lightweight cushioned running shoes with breathable mesh and grippy outsole for road and trail running.", "shoes running sport trail fitness", 115.0, 27, 4.5),
    ("SP-3002", "FlexMat Yoga Mat", "زیرانداز یوگا FlexMat", "sports", "Non-slip 6 mm yoga mat with carry strap, eco-friendly TPE material for yoga, pilates and home workouts.", "yoga mat fitness home workout pilates", 25.0, 45, 4.4),
    ("SP-3003", "HydroSteel Water Bottle", "بطری آب HydroSteel", "sports", "Insulated stainless steel bottle keeps drinks cold for 24 hours or hot for 12. Leak-proof, 750 ml.", "bottle water gym travel hiking", 19.0, 120, 4.7),
    ("BK-4001", "Clean Code Handbook", "کتاب کد تمیز", "books", "A practical guide to writing readable, maintainable software with real-world refactoring examples.", "book programming software developer gift", 32.0, 15, 4.8),
    ("BK-4002", "The Home Barista", "کتاب باریستای خانگی", "books", "Illustrated guide to brewing great coffee at home: espresso, pour-over and latte art basics.", "book coffee barista gift kitchen", 24.0, 11, 4.4),
]

ORDERS = [
    ("ORD-1001", "delivered", "EL-1001", 129.0, "DHL", -6),
    ("ORD-1002", "shipped", "EL-1005,EL-1006", 144.0, "UPS", 2),
    ("ORD-1003", "processing", "HM-2001,BK-4002", 243.0, "", 5),
    ("ORD-1004", "cancelled", "SP-3001", 115.0, "", 0),
    ("ORD-1005", "out_for_delivery", "EL-1009,SP-3003", 168.0, "FedEx", 0),
]


def seed(session) -> None:
    if session.scalar(select(Product.id).limit(1)) is not None:
        return
    for sku, name, name_fa, cat, desc, tags, price, stock, rating in PRODUCTS:
        session.add(Product(sku=sku, name=name, name_fa=name_fa, category=cat, description=desc,
                            tags=tags, price=price, stock=stock, rating=rating))
    today = datetime.now(timezone.utc).date()
    for number, status, items, total, carrier, eta_days in ORDERS:
        eta = "" if status == "cancelled" else (today + timedelta(days=eta_days)).isoformat()
        session.add(Order(number=number, status=status, items=items, total=total, carrier=carrier, eta=eta))
    session.commit()
