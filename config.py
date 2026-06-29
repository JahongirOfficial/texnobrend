import os

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    # If you run locally, create a .env file with BOT_TOKEN=your_token
    # If deploying on Railway, set BOT_TOKEN in variables
    raise ValueError("BOT_TOKEN is not set in environment variables or .env file!")


admin_ids_str = os.getenv("ADMIN_IDS", "5027595868")
ADMIN_IDS = [int(x.strip()) for x in admin_ids_str.split(",") if x.strip()]

DB_PATH = os.getenv("DB_PATH", "texnobrend.db")
ITEMS_PER_PAGE = int(os.getenv("ITEMS_PER_PAGE", "6"))
STICKER_FILE = os.getenv("STICKER_FILE", "stickers.json")

# ── To'lov provayderlari (Telegram Invoices) ────────────────────────
CLICK_PROVIDER_TOKEN = os.getenv("CLICK", "")
PAYME_PROVIDER_TOKEN = os.getenv("PAYME", "")



# ── Do'kon ma'lumotlari ───────────────────────────────────────────
SHOP_NAME    = os.getenv("SHOP_NAME", "Texnobrend")
CONTACT_PHONE    = os.getenv("CONTACT_PHONE", "+998 90 000 00 00")
CONTACT_USERNAME = os.getenv("CONTACT_USERNAME", "@texnobrend_uz")
SUPPORT_ADMIN_ID = int(os.getenv("SUPPORT_ADMIN_ID", "5027595868"))


SHOP_LOCATION = {
    "lat":     41.2995,
    "lon":     69.2401,
    "title":   "Texnobrend Do'koni",
    "address": "Toshkent sh., Chilonzor tumani, Bunyodkor ko'chasi 1A",
}

# ── Majburiy obuna kanallari ─────────────────────────────────────
# Bo'sh qoldiring = obuna tekshiruvi yo'q
REQUIRED_CHANNELS: list[dict] = [
    # {"username": "@texnobrend_kanal", "title": "Texnobrend Kanal", "url": "https://t.me/texnobrend_kanal"},
]

# ── Message Effects (Bot API 7.4) ────────────────────────────────
EFFECTS = {
    "fire":      "5104841245755180586",
    "heart":     "5159385139981059251",
    "thumbsup":  "5107584321108051014",
    "confetti":  "5046509860389126442",
    "fireworks": "5044101728060834560",
}

DEFAULT_STICKERS: dict[str, str] = {}  # loaded from stickers.json
