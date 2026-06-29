from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import (
    SHOP_NAME, CONTACT_PHONE, CONTACT_USERNAME,
    SUPPORT_ADMIN_ID, SHOP_LOCATION, REQUIRED_CHANNELS, ADMIN_IDS,
)
from database import upsert_user
from keyboards import main_menu_kb, subscription_kb
from utils import send_sticker, send_with_effect
from states import Calculator

router = Router()


@router.message(F.text == "❌ Bekor qilish")
async def global_cancel(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())


# ──────────────── subscription check helper ────────────────

async def is_subscribed(bot, user_id: int) -> bool:
    if not REQUIRED_CHANNELS:
        return True
    if user_id in ADMIN_IDS:
        return True
    for ch in REQUIRED_CHANNELS:
        try:
            member = await bot.get_chat_member(ch["username"], user_id)
            if member.status in ("left", "kicked", "banned"):
                return False
        except Exception:
            return False
    return True


# ──────────────── /start ────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user = message.from_user
    await upsert_user(user.id, user.username, user.full_name)

    bot = message.bot
    if not await is_subscribed(bot, user.id):
        await message.answer(
            f"👋 Salom, <b>{user.first_name}</b>!\n\n"
            f"⚠️ <b>{SHOP_NAME}</b> botidan foydalanish uchun "
            f"quyidagi kanallarga obuna bo'ling:",
            reply_markup=subscription_kb(),
            parse_mode="HTML",
        )
        return

    await send_sticker(bot, message.chat.id, "welcome")
    await send_with_effect(
        bot, message.chat.id,
        f"👋 Salom, <b>{user.first_name}</b>!\n\n"
        f"🏪 <b>{SHOP_NAME}</b> botiga xush kelibsiz!\n\n"
        f"📱 Bizda eng yangi va sifatli texnologik mahsulotlar mavjud.\n"
        f"Qulay narxlar, tez yetkazib berish, kafolat!\n\n"
        f"👇 Quyidagi menyudan tanlang:",
        effect_key="confetti",
        reply_markup=main_menu_kb(),
    )


# ──────────────── subscription check callback ────────────────

@router.callback_query(F.data == "check_subscription")
async def check_sub(callback: CallbackQuery):
    bot = callback.bot
    user_id = callback.from_user.id

    if await is_subscribed(bot, user_id):
        await callback.message.delete()
        user = callback.from_user
        await upsert_user(user_id, user.username, user.full_name)
        await send_sticker(bot, callback.message.chat.id, "welcome")
        await send_with_effect(
            bot, callback.message.chat.id,
            f"✅ <b>Obuna tasdiqlandi!</b>\n\n"
            f"👋 Salom, <b>{user.first_name}</b>!\n"
            f"🏪 <b>{SHOP_NAME}</b> botiga xush kelibsiz!",
            effect_key="confetti",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.answer(
            "❌ Hali barcha kanallarga obuna bo'lmadingiz!", show_alert=True
        )


# ──────────────── main menu callback ────────────────

@router.callback_query(F.data == "main_menu")
async def cb_main_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "🏠 <b>Bosh menyu</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
    await callback.answer()



# ──────────────── noop ────────────────

@router.callback_query(F.data == "noop")
async def cb_noop(callback: CallbackQuery):
    await callback.answer()


# ──────────────── support ────────────────

@router.message(F.text == "🆘 Yordam")
async def menu_support(message: Message):
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="💬 Admin bilan bog'lanish",
        url=f"tg://user?id={SUPPORT_ADMIN_ID}",
    ))
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))

    await message.answer(
        f"🆘 <b>Yordam va qo'llab-quvvatlash</b>\n\n"
        f"📞 Telefon: <b>{CONTACT_PHONE}</b>\n"
        f"💬 Telegram: <b>{CONTACT_USERNAME}</b>\n\n"
        f"🕐 Ish vaqti: Du-Sha, 09:00 — 20:00\n\n"
        f"Savollaringiz bo'lsa, quyidagi tugma orqali admin bilan bog'laning:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# ──────────────── location ────────────────

@router.message(F.text == "📍 Manzil")
async def menu_location(message: Message):
    loc = SHOP_LOCATION
    await message.answer_venue(
        latitude=loc["lat"],
        longitude=loc["lon"],
        title=loc["title"],
        address=loc["address"],
    )
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(
        text="🗺 Google Maps da ko'rish",
        url=f"https://maps.google.com/?q={loc['lat']},{loc['lon']}",
    ))
    await message.answer(
        f"📍 <b>{loc['title']}</b>\n"
        f"📌 {loc['address']}\n\n"
        f"🕐 Ish vaqti: Du-Sha, 09:00 — 20:00",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# ──────────────── calculator ────────────────

@router.message(F.text == "🧮 Kalkulyator")
async def menu_calculator(message: Message, state: FSMContext):
    await state.set_state(Calculator.price)
    from keyboards import cancel_kb
    await message.answer(
        "🧮 <b>Narx kalkulyatori</b>\n\n"
        "Mahsulot narxini kiriting (so'mda):\n"
        "<i>Misol: 5990000</i>",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(Calculator.price, F.text)
async def calc_price(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    text = message.text.replace(" ", "").replace(",", "")
    if not text.isdigit():
        await message.answer("❌ Raqam kiriting! Misol: <code>5990000</code>", parse_mode="HTML")
        return

    await state.update_data(price=int(text))
    from keyboards import cancel_kb
    await state.set_state(Calculator.quantity)
    await message.answer(
        "📦 Nechta olmoqchisiz? (Miqdorni kiriting):",
        reply_markup=cancel_kb(),
    )


@router.message(Calculator.price)
async def calc_price_invalid(message: Message):
    await message.answer("❌ Iltimos, narxni faqat son shaklida kiriting!")


@router.message(Calculator.quantity, F.text)
async def calc_quantity(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    text = message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await message.answer("❌ Musbat son kiriting!")
        return

    data = await state.get_data()
    price = data["price"]
    qty = int(text)
    total = price * qty


    def fmt(n):
        return f"{n:,}".replace(",", " ")

    installment_3 = total // 3
    installment_6 = total // 6
    installment_12 = total // 12

    await state.clear()
    await message.answer(
        f"🧮 <b>Hisob-kitob natijasi</b>\n\n"
        f"💰 Narx: <b>{fmt(price)} so'm</b>\n"
        f"📦 Miqdor: <b>{qty} ta</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"💵 <b>Jami: {fmt(total)} so'm</b>\n\n"
        f"📅 <b>Muddatli to'lov:</b>\n"
        f"  • 3 oyga: <b>{fmt(installment_3)} so'm/oy</b>\n"
        f"  • 6 oyga: <b>{fmt(installment_6)} so'm/oy</b>\n"
        f"  • 12 oyga: <b>{fmt(installment_12)} so'm/oy</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(Calculator.quantity)
async def calc_quantity_invalid(message: Message):
    await message.answer("❌ Iltimos, miqdorni faqat son shaklida kiriting!")



# ──────────────── about ────────────────

@router.message(F.text == "ℹ️ Bot haqida")
async def menu_about(message: Message):
    await message.answer(
        f"ℹ️ <b>{SHOP_NAME} haqida</b>\n\n"
        f"🏪 Biz eng yangi va sifatli texnologik mahsulotlarni taqdim etamiz.\n\n"
        f"📦 Mahsulotlar:\n"
        f"  • Smartfonlar (Samsung, Apple, Xiaomi)\n"
        f"  • Noutbuklar (Apple, Lenovo, ASUS)\n"
        f"  • Televizorlar (Samsung, LG, Xiaomi)\n"
        f"  • Maishiy texnika (Artel)\n"
        f"  • Naushniklar va Smart soatlar\n\n"
        f"✅ Kafolat: 1-2 yil\n"
        f"🚀 Yetkazib berish: 1-3 kun\n"
        f"💳 To'lov: Click, Payme, Naqd\n\n"
        f"📞 {CONTACT_PHONE}\n"
        f"💬 {CONTACT_USERNAME}",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
