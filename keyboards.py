from aiogram.types import (
    InlineKeyboardButton, InlineKeyboardMarkup,
    ReplyKeyboardMarkup, KeyboardButton,
    ReplyKeyboardRemove, CopyTextButton,
)
from aiogram.enums import ButtonStyle
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from config import REQUIRED_CHANNELS, SUPPORT_ADMIN_ID


def _b(text, cd, **kw):
    return InlineKeyboardButton(text=text, callback_data=cd, **kw)


def _url(text, url):
    return InlineKeyboardButton(text=text, url=url)


def _copy(text, copy_text):
    return InlineKeyboardButton(text=text, copy_text=CopyTextButton(text=copy_text))


# ──────────────── main menu ────────────────

def main_menu_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Mahsulotlar"), KeyboardButton(text="🔍 Qidirish")],
            [KeyboardButton(text="🛍 Savatcha"), KeyboardButton(text="📋 Buyurtmalarim")],
            [KeyboardButton(text="🆘 Yordam"), KeyboardButton(text="📍 Manzil")],
            [KeyboardButton(text="🧮 Kalkulyator"), KeyboardButton(text="ℹ️ Bot haqida")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Menyudan tanlang...",
    )


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Bekor qilish")]],
        resize_keyboard=True,
    )


def remove_kb():
    return ReplyKeyboardRemove()


# ──────────────── subscription ────────────────

def subscription_kb():
    builder = InlineKeyboardBuilder()
    for ch in REQUIRED_CHANNELS:
        builder.row(_url(f"📢 {ch['title']}", ch["url"]))
    builder.row(_b("✅ Obunani tekshirish", "check_subscription", style=ButtonStyle.SUCCESS))
    return builder.as_markup()


# ──────────────── catalog ────────────────

def brands_kb(brands: list):
    builder = InlineKeyboardBuilder()
    for brand in brands:
        builder.button(
            text=f"🏷 {brand}",
            callback_data=f"brand:{brand}",
            style=ButtonStyle.PRIMARY,
        )
    builder.adjust(2)
    builder.row(_b("🗂 Barcha kategoriyalar", "all_categories"))
    builder.row(_b("🔍 Qidirish", "search"), _b("◀️ Bosh menyu", "main_menu"))
    return builder.as_markup()


def categories_kb(categories, brand=None):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        # cat['name'] already contains emoji (e.g. "📱 Smartfonlar"), don't add icon again
        builder.button(
            text=cat["name"],
            callback_data=f"cat:{cat['id']}:1",
            style=ButtonStyle.PRIMARY,
        )
    builder.adjust(2)
    back_cd = "all_categories" if brand else "main_menu"
    builder.row(_b("◀️ Orqaga", back_cd))
    return builder.as_markup()


def products_kb(products, category_id, page, total, per_page, brand=None):
    builder = InlineKeyboardBuilder()
    for p in products:
        price_str = f"{p['price']:,}".replace(",", " ")
        stock_icon = "✅" if p["stock"] > 0 else "❌"
        builder.button(
            text=f"{stock_icon} {p['name']} — {price_str} so'm",
            callback_data=f"prod:{p['id']}",
        )
    builder.adjust(1)
    total_pages = (total + per_page - 1) // per_page or 1
    nav = []
    if page > 1:
        nav.append(_b("◀️", f"cat:{category_id}:{page-1}"))
    nav.append(_b(f"📄 {page}/{total_pages}", "noop"))
    if page < total_pages:
        nav.append(_b("▶️", f"cat:{category_id}:{page+1}"))
    if nav:
        builder.row(*nav)
    back_cd = f"brand:{brand}" if brand else "all_categories"
    builder.row(_b("◀️ Kategoriyalar", back_cd), _b("🏠 Bosh", "main_menu"))
    return builder.as_markup()



def product_detail_kb(product_id, cat_id, added=False):
    builder = InlineKeyboardBuilder()
    if added:
        builder.row(
            _b("✅ Savatga qo'shildi", f"cart_add:{product_id}", style=ButtonStyle.PRIMARY),
        )
    else:
        builder.row(
            _b("🛒 Savatga qo'shish", f"cart_add:{product_id}", style=ButtonStyle.SUCCESS),
        )
    builder.row(
        _b("⚡ Tez buyurtma", f"fast_order:{product_id}", style=ButtonStyle.PRIMARY),
    )
    builder.row(
        _b("◀️ Orqaga", f"cat:{cat_id}:1"),
        _b("🏠 Bosh menyu", "main_menu"),
    )
    return builder.as_markup()



# ──────────────── cart ────────────────

def cart_kb(has_items=True):
    builder = InlineKeyboardBuilder()
    if has_items:
        builder.row(_b("✅ Buyurtma berish", "checkout", style=ButtonStyle.SUCCESS))
        builder.row(_b("🗑 Savatni tozalash", "cart_clear", style=ButtonStyle.DANGER))
    builder.row(_b("🛒 Mahsulotlar", "all_categories"), _b("🏠 Bosh menyu", "main_menu"))
    return builder.as_markup()


def cart_item_kb(product_id, qty):
    builder = InlineKeyboardBuilder()
    builder.row(
        _b("➖", f"qty_dec:{product_id}"),
        _b(f"  {qty}  ", "noop"),
        _b("➕", f"qty_inc:{product_id}"),
    )
    builder.row(_b("🗑 O'chirish", f"cart_remove:{product_id}", style=ButtonStyle.DANGER))
    builder.row(_b("◀️ Savat", "cart"), _b("✅ Buyurtma", "checkout", style=ButtonStyle.SUCCESS))
    return builder.as_markup()


def checkout_phone_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Raqamni yuborish", request_contact=True)],
            [KeyboardButton(text="❌ Bekor qilish")],
        ],
        resize_keyboard=True,
    )


def checkout_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.row(_b("✅ Tasdiqlash", "order_confirm", style=ButtonStyle.SUCCESS))
    builder.row(_b("✏️ O'zgartirish", "order_edit"), _b("❌ Bekor", "order_cancel", style=ButtonStyle.DANGER))
    return builder.as_markup()


# ──────────────── payment ────────────────

def payment_kb(order_id):
    builder = InlineKeyboardBuilder()
    builder.row(
        _b("💳 Click orqali", f"pay_click:{order_id}", style=ButtonStyle.PRIMARY),
        _b("💚 Payme orqali", f"pay_payme:{order_id}", style=ButtonStyle.SUCCESS),
    )
    builder.row(_b("💵 Naqd to'lash", f"pay_cash:{order_id}"))
    builder.row(_b("📋 Buyurtmalarim", "my_orders"))
    return builder.as_markup()


# ──────────────── orders ────────────────

def orders_kb():
    builder = InlineKeyboardBuilder()
    builder.row(_b("🛒 Mahsulotlar", "all_categories"), _b("🏠 Bosh menyu", "main_menu"))
    return builder.as_markup()


def order_detail_kb(order_id):
    builder = InlineKeyboardBuilder()
    builder.row(_copy(f"📋 #{order_id} nusxalash", f"Buyurtma #{order_id}"))
    builder.row(_b("◀️ Buyurtmalar", "my_orders"), _b("🏠 Bosh menyu", "main_menu"))
    return builder.as_markup()


# ──────────────── admin panel ────────────────

def admin_panel_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            _b("📊 Statistika", "adm_stats"),
            _b("👥 Foydalanuvchilar", "adm_users:1"),
        ],
        [
            _b("📦 Mahsulotlar", "adm_products:1"),
            _b("📋 Buyurtmalar", "adm_orders:all:1"),
        ],
        [
            _b("📢 Broadcast", "adm_broadcast"),
            _b("🖼 Stikerlar", "adm_stickers"),
        ],
        [
            _b("⚙️ Sozlamalar", "adm_settings"),
        ],
    ])


def admin_back_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [_b("◀️ Admin panel", "adm_panel")]
    ])


# ──────────────── admin users ────────────────

def admin_users_kb(users, page, total, per_page=10):
    builder = InlineKeyboardBuilder()
    for u in users:
        name = u["full_name"] or u["username"] or str(u["telegram_id"])
        banned = "🚫 " if u["is_banned"] else ""
        builder.button(text=f"{banned}{name}", callback_data=f"adm_user:{u['telegram_id']}")
    builder.adjust(2)
    total_pages = (total + per_page - 1) // per_page or 1
    nav = []
    if page > 1:
        nav.append(_b("◀️", f"adm_users:{page-1}"))
    nav.append(_b(f"{page}/{total_pages}", "noop"))
    if page < total_pages:
        nav.append(_b("▶️", f"adm_users:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(_b("◀️ Panel", "adm_panel"))
    return builder.as_markup()


def admin_user_detail_kb(telegram_id, is_banned):
    builder = InlineKeyboardBuilder()
    builder.row(_copy("📋 ID nusxalash", str(telegram_id)))
    if is_banned:
        builder.row(_b("✅ Blokdan chiqarish", f"adm_unban:{telegram_id}", style=ButtonStyle.SUCCESS))
    else:
        builder.row(_b("🚫 Bloklash", f"adm_ban:{telegram_id}", style=ButtonStyle.DANGER))
    builder.row(_b("✉️ Xabar yuborish", f"adm_msg:{telegram_id}", style=ButtonStyle.PRIMARY))
    builder.row(_b("◀️ Foydalanuvchilar", "adm_users:1"))
    return builder.as_markup()


# ──────────────── admin products ────────────────

def admin_products_kb(products, page, total, per_page=8):
    builder = InlineKeyboardBuilder()
    for p in products:
        avail = "✅" if p["is_available"] else "❌"
        builder.button(text=f"{avail} {p['name'][:30]}", callback_data=f"adm_prod:{p['id']}")
    builder.adjust(1)
    total_pages = (total + per_page - 1) // per_page or 1
    nav = []
    if page > 1:
        nav.append(_b("◀️", f"adm_products:{page-1}"))
    nav.append(_b(f"{page}/{total_pages}", "noop"))
    if page < total_pages:
        nav.append(_b("▶️", f"adm_products:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(_b("➕ Mahsulot qo'shish", "adm_prod_add", style=ButtonStyle.SUCCESS))
    builder.row(_b("◀️ Panel", "adm_panel"))
    return builder.as_markup()


def admin_product_detail_kb(product_id, is_available):
    builder = InlineKeyboardBuilder()
    toggle_text = "❌ O'chirish" if is_available else "✅ Yoqish"
    toggle_style = ButtonStyle.DANGER if is_available else ButtonStyle.SUCCESS
    builder.row(_b(toggle_text, f"adm_prod_toggle:{product_id}", style=toggle_style))
    builder.row(_b("✏️ Tahrirlash", f"adm_prod_edit:{product_id}", style=ButtonStyle.PRIMARY))
    builder.row(_b("🖼 Rasm o'zgartirish", f"adm_prod_photo:{product_id}", style=ButtonStyle.PRIMARY))
    builder.row(_b("🗑 O'chirish", f"adm_prod_del:{product_id}", style=ButtonStyle.DANGER))
    builder.row(_b("◀️ Mahsulotlar", "adm_products:1"))
    return builder.as_markup()


def admin_product_edit_kb(product_id):
    fields = [
        ("📝 Nomi", "name"), ("📄 Tavsif", "description"),
        ("💰 Narxi", "price"), ("🏷 Eski narx", "old_price"),
        ("📦 Soni", "stock"),
    ]
    builder = InlineKeyboardBuilder()
    for label, field in fields:
        builder.button(text=label, callback_data=f"adm_edit_field:{product_id}:{field}")
    builder.adjust(2)
    builder.row(_b("◀️ Orqaga", f"adm_prod:{product_id}"))
    return builder.as_markup()


# ──────────────── admin orders ────────────────

def admin_orders_filter_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            _b("🔄 Hammasi", "adm_orders:all:1"),
            _b("⏳ Kutmoqda", "adm_orders:pending:1"),
        ],
        [
            _b("📦 Jarayonda", "adm_orders:processing:1"),
            _b("✅ Yetkazildi", "adm_orders:completed:1"),
        ],
        [
            _b("❌ Bekor", "adm_orders:cancelled:1"),
        ],
        [_b("◀️ Panel", "adm_panel")],
    ])


def admin_orders_kb(orders, status, page, total, per_page=8):
    STATUS_ICONS = {
        "pending": "⏳", "processing": "📦",
        "completed": "✅", "cancelled": "❌",
    }
    builder = InlineKeyboardBuilder()
    for o in orders:
        icon = STATUS_ICONS.get(o["status"], "❓")
        name = o["full_name"] or o["username"] or str(o["user_id"])
        builder.button(
            text=f"{icon} #{o['id']} — {name}",
            callback_data=f"adm_order:{o['id']}"
        )
    builder.adjust(1)
    total_pages = (total + per_page - 1) // per_page or 1
    nav = []
    if page > 1:
        nav.append(_b("◀️", f"adm_orders:{status}:{page-1}"))
    nav.append(_b(f"{page}/{total_pages}", "noop"))
    if page < total_pages:
        nav.append(_b("▶️", f"adm_orders:{status}:{page+1}"))
    if nav:
        builder.row(*nav)
    builder.row(_b("🔽 Filter", "adm_orders_filter"))
    builder.row(_b("◀️ Panel", "adm_panel"))
    return builder.as_markup()


def admin_order_detail_kb(order_id, current_status):
    STATUS_TRANSITIONS = {
        "pending": [("📦 Jarayonga", "processing"), ("❌ Bekor qilish", "cancelled")],
        "processing": [("✅ Yetkazildi", "completed"), ("❌ Bekor qilish", "cancelled")],
        "completed": [],
        "cancelled": [("🔄 Tiklash", "pending")],
    }
    builder = InlineKeyboardBuilder()
    builder.row(_copy(f"📋 #{order_id} nusxalash", f"Buyurtma #{order_id}"))
    for label, new_status in STATUS_TRANSITIONS.get(current_status, []):
        style = ButtonStyle.SUCCESS if new_status == "completed" else ButtonStyle.DANGER if new_status == "cancelled" else ButtonStyle.PRIMARY
        builder.row(_b(label, f"adm_order_status:{order_id}:{new_status}", style=style))
    builder.row(_b("◀️ Buyurtmalar", "adm_orders:all:1"))
    return builder.as_markup()


# ──────────────── admin settings ────────────────

def admin_settings_kb():
    builder = InlineKeyboardBuilder()
    builder.row(_b("💰 Global chegirma", "adm_set_discount", style=ButtonStyle.PRIMARY))
    builder.row(_b("◀️ Panel", "adm_panel"))
    return builder.as_markup()


# ──────────────── admin stickers ────────────────

def admin_stickers_kb(sticker_keys):
    builder = InlineKeyboardBuilder()
    for key in sticker_keys:
        builder.button(text=f"🖼 {key}", callback_data=f"adm_sticker_set:{key}")
    builder.adjust(3)
    builder.row(_b("◀️ Panel", "adm_panel"))
    return builder.as_markup()


# ──────────────── broadcast ────────────────

def broadcast_confirm_kb():
    builder = InlineKeyboardBuilder()
    builder.row(
        _b("✅ Yuborish", "adm_broadcast_send", style=ButtonStyle.SUCCESS),
        _b("❌ Bekor", "adm_broadcast_cancel", style=ButtonStyle.DANGER),
    )
    return builder.as_markup()
