import json
from config import STICKER_FILE, EFFECTS


def load_stickers() -> dict:
    try:
        with open(STICKER_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_sticker(key: str, file_id: str):
    data = load_stickers()
    data[key] = file_id
    with open(STICKER_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def send_sticker(bot, chat_id, key: str):
    stickers = load_stickers()
    file_id = stickers.get(key)
    if file_id:
        try:
            await bot.send_sticker(chat_id, file_id)
        except Exception:
            pass


async def send_with_effect(bot, chat_id, text: str, effect_key: str = None,
                           reply_markup=None, parse_mode="HTML", **kwargs):
    effect_id = EFFECTS.get(effect_key) if effect_key else None
    params = dict(chat_id=chat_id, text=text, parse_mode=parse_mode, **kwargs)
    if reply_markup:
        params["reply_markup"] = reply_markup
    if effect_id:
        params["message_effect_id"] = effect_id
    try:
        return await bot.send_message(**params)
    except Exception:
        if "message_effect_id" in params:
            del params["message_effect_id"]
        return await bot.send_message(**params)


def fmt_price(price) -> str:
    if not price:
        return "0"
    return f"{int(price):,}".replace(",", " ")


def _row_get(row, key: str, default=""):
    """Safe getter for sqlite3.Row (no .get() method)."""
    try:
        return row[key] or default
    except (KeyError, IndexError):
        return default


def make_product_text(product) -> str:
    name = product["name"]
    price = fmt_price(product["price"])
    old_price_val = product["old_price"]
    description = product["description"] or "Tavsif mavjud emas"
    stock = product["stock"]
    brand = _row_get(product, "brand")
    cat_name = _row_get(product, "cat_name")

    discount = ""
    if old_price_val and old_price_val > product["price"]:
        pct = int(100 - (product["price"] / old_price_val * 100))
        discount = f"🔥 <b>-{pct}% chegirma!</b>\n"

    if stock > 10:
        stock_line = "✅ Mavjud"
    elif stock > 0:
        stock_line = f"⚠️ Faqat {stock} ta qoldi!"
    else:
        stock_line = "❌ Mavjud emas"

    lines = [f"<b>{name}</b>"]
    if brand:
        lines.append(f"🏷 {brand} · {cat_name}")
    lines.append("")
    lines.append(f"📝 {description}")
    lines.append("")
    if discount:
        lines.append(discount.strip())
    lines.append(f"💰 <b>{price} so'm</b>")
    if old_price_val:
        lines.append(f"<s>{fmt_price(old_price_val)} so'm</s>")
    lines.append(f"📦 {stock_line}")

    return "\n".join(lines)
