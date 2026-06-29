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
            f"👋 Assalomu alaykum, <b>{user.first_name}</b>!\n\n"
            f"⚠️ Xizmatlarimizdan to'liq foydalanish uchun, iltimos, "
            f"quyidagi rasmiy kanallarimizga a'zo bo'ling:",
            reply_markup=subscription_kb(),
            parse_mode="HTML",
        )
        return

    await send_sticker(bot, message.chat.id, "welcome")
    await send_with_effect(
        bot, message.chat.id,
        f"👋 Assalomu alaykum, hurmatli <b>{user.first_name}</b>!\n\n"
        f"🏪 <b>{SHOP_NAME}</b> internet-do'konimizga xush kelibsiz! 😊\n\n"
        f"📱 Bu yerda eng yangi va original gadjetlarni eng qulay narxlarda topishingiz mumkin. Rasmiy kafolat va tezkor yetkazib berish bilan xizmatingizdamiz!\n\n"
        f"Xarid qilishni boshlash uchun quyidagi menyudan foydalaning: 👇",
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
            f"🎉 <b>Obuna muvaffaqiyatli tasdiqlandi!</b>\n\n"
            f"👋 Assalomu alaykum, hurmatli <b>{user.first_name}</b>!\n"
            f"🏪 <b>{SHOP_NAME}</b> do'konimizga xush kelibsiz! Marhamat, quyidagi menyudan foydalaning:",
            effect_key="confetti",
            reply_markup=main_menu_kb(),
        )
    else:
        await callback.answer(
            "⚠️ Kechirasiz, hali barcha kanallarga obuna bo'lmadingiz. Iltimos, obunani tekshirib qayta urining!", show_alert=True
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
        f"🆘 <b>Qo'llab-quvvatlash va Aloqa bo'limi</b>\n\n"
        f"Hurmatli mijoz, agar sizda biror savol, taklif yoki texnik muammolar yuzaga kelgan bo'lsa, istalgan vaqtda bizga murojaat qilishingiz mumkin. Biz sizga yordam berishdan mamnunmiz!\n\n"
        f"📞 <b>Aloqa telefoni:</b> {CONTACT_PHONE}\n"
        f"💬 <b>Telegram profilimiz:</b> {CONTACT_USERNAME}\n\n"
        f"🕐 <b>Ish vaqtimiz:</b> Dushanba – Yakshanba, 09:00 dan 20:00 gacha\n\n"
        f"Pastdagi tugma orqali bevosita administratorimiz bilan tezkor bog'lanishingiz ham mumkin:",
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
        f"📍 <b>{loc['title']} do'konimiz manzili:</b>\n"
        f"📌 {loc['address']}\n\n"
        f"🕐 <b>Ish vaqtimiz:</b> Dushanba – Yakshanba, 09:00 dan 20:00 gacha. Tashrif buyurishingiz mumkin, sizni kutib qolamiz!",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


# ──────────────── calculator ────────────────

@router.message(F.text == "🧮 Kalkulyator")
async def menu_calculator(message: Message, state: FSMContext):
    await state.set_state(Calculator.price)
    from keyboards import cancel_kb
    await message.answer(
        "🧮 <b>Muddatli to'lov kalkulyatori</b>\n\n"
        "Iltimos, mahsulot narxini kiriting (masalan: <code>5990000</code>):",
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
        await message.answer("⚠️ Iltimos, narxni faqat sonlarda kiriting (masalan: <code>5990000</code>):", parse_mode="HTML")
        return

    await state.update_data(price=int(text))
    from keyboards import cancel_kb
    await state.set_state(Calculator.quantity)
    await message.answer(
        "📦 Tanlangan mahsulotdan nechta xarid qilmoqchisiz? (Miqdorini yozing):",
        reply_markup=cancel_kb(),
    )


@router.message(Calculator.price)
async def calc_price_invalid(message: Message):
    await message.answer("⚠️ Iltimos, mahsulot narxini faqat sonlar bilan yozib yuboring!")


@router.message(Calculator.quantity, F.text)
async def calc_quantity(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    text = message.text.strip()
    if not text.isdigit() or int(text) < 1:
        await message.answer("⚠️ Iltimos, miqdorni 1 dan katta musbat son ko'rinishida kiriting!")
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
        f"🧮 <b>Hisob-kitob natijasi:</b>\n\n"
        f"💰 Mahsulot narxi: <b>{fmt(price)} so'm</b>\n"
        f"📦 Miqdori: <b>{qty} ta</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"💵 <b>Jami summa: {fmt(total)} so'm</b>\n\n"
        f"📅 <b>Bo'lib to'lash variantlari:</b>\n"
        f"  • 3 oyga: <b>{fmt(installment_3)} so'm/oy</b>\n"
        f"  • 6 oyga: <b>{fmt(installment_6)} so'm/oy</b>\n"
        f"  • 12 oyga: <b>{fmt(installment_12)} so'm/oy</b>",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )


@router.message(Calculator.quantity)
async def calc_quantity_invalid(message: Message):
    await message.answer("⚠️ Iltimos, miqdorni faqat son ko'rinishida yozib yuboring!")



# ──────────────── about ────────────────

@router.message(F.text == "ℹ️ Bot haqida")
async def menu_about(message: Message):
    await message.answer(
        f"ℹ️ <b>{SHOP_NAME} do'koni haqida</b>\n\n"
        f"🏪 Biz eng so'nggi rusumdagi va 100% original texnologik mahsulotlarni taqdim etishdan faxrlanamiz. Do'konimiz orqali uyingizdan chiqmasdan turib xaridlarni amalga oshiring!\n\n"
        f"📦 <b>Bizning mahsulotlarimiz:</b>\n"
        f"  • Zamonaviy smartfonlar (Apple, Samsung, Xiaomi)\n"
        f"  • Kuchli noutbuklar (Apple MacBook, Lenovo, ASUS)\n"
        f"  • Katta ekranli televizorlar (Samsung, LG, Xiaomi)\n"
        f"  • Ishonchli maishiy texnikalar (Artel va boshqalar)\n"
        f"  • Sifatli naushniklar va smart-soatlar\n\n"
        f"✅ <b>Afzalliklarimiz:</b>\n"
        f"  🛡 1-2 yilgacha rasmiy kafolat\n"
        f"  🚀 O'zbekiston bo'ylab tezkor yetkazib berish (1-3 kun)\n"
        f"  💳 Click, Payme yoki eshik oldida naqd to'lash imkoniyati\n\n"
        f"📞 Telefon: {CONTACT_PHONE}\n"
        f"💬 Telegram: {CONTACT_USERNAME}",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )
