from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

import database as db
from keyboards import orders_kb, order_detail_kb, main_menu_kb
from utils import fmt_price

router = Router()

STATUS_ICONS = {
    "pending": "⏳ Kutmoqda",
    "processing": "📦 Jarayonda",
    "completed": "✅ Yetkazildi",
    "cancelled": "❌ Bekor qilindi",
}


@router.message(F.text == "📋 Buyurtmalarim")
async def menu_orders(message: Message):
    orders = await db.get_user_orders(message.from_user.id)
    if not orders:
        await message.answer(
            "📋 <b>Sizning buyurtmalaringiz tarixi</b>\n\nSiz hali birorta ham buyurtma bermagansiz. Mahsulotlar katalogiga o'tib, o'zingizga yoqqan mahsulotni tanlashingiz va buyurtma qilishingiz mumkin.",
            reply_markup=orders_kb(),
            parse_mode="HTML",
        )
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for o in orders:
        status = STATUS_ICONS.get(o["status"], o["status"])
        price = fmt_price(o["total_price"])
        date = str(o["created_at"])[:10]
        builder.button(
            text=f"#{o['id']} {status} — {price} so'm ({date})",
            callback_data=f"order:{o['id']}",
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))

    await message.answer(
        f"📋 <b>Sizning buyurtmalaringiz ro'yxati</b> (jami {len(orders)} ta):",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "my_orders")
async def cb_my_orders(callback: CallbackQuery):
    orders = await db.get_user_orders(callback.from_user.id)
    if not orders:
        await callback.message.edit_text(
            "📋 <b>Sizning buyurtmalaringiz tarixi</b>\n\nSiz hali birorta ham buyurtma bermagansiz. Mahsulotlar katalogiga o'tib, o'zingizga yoqqan mahsulotni tanlashingiz va buyurtma qilishingiz mumkin.",
            reply_markup=orders_kb(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    from aiogram.utils.keyboard import InlineKeyboardBuilder
    from aiogram.types import InlineKeyboardButton

    builder = InlineKeyboardBuilder()
    for o in orders:
        status = STATUS_ICONS.get(o["status"], o["status"])
        price = fmt_price(o["total_price"])
        date = str(o["created_at"])[:10]
        builder.button(
            text=f"#{o['id']} {status} — {price} so'm ({date})",
            callback_data=f"order:{o['id']}",
        )
    builder.adjust(1)
    builder.row(InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"))

    try:
        await callback.message.edit_text(
            f"📋 <b>Buyurtmalarim</b> ({len(orders)} ta):",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    except Exception:
        await callback.message.answer(
            f"📋 <b>Buyurtmalarim</b> ({len(orders)} ta):",
            reply_markup=builder.as_markup(),
            parse_mode="HTML",
        )
    await callback.answer()


@router.callback_query(F.data.startswith("order:"))
async def cb_order_detail(callback: CallbackQuery):
    order_id = int(callback.data.split(":")[1])
    order, items = await db.get_order(order_id)

    if not order or order["user_id"] != callback.from_user.id:
        await callback.answer("Buyurtma topilmadi", show_alert=True)
        return

    status = STATUS_ICONS.get(order["status"], order["status"])
    items_text = "\n".join(
        f"• {i['name']} × {i['quantity']} = {fmt_price(i['price'] * i['quantity'])} so'm"
        for i in items
    )

    text = (
        f"📋 <b>Buyurtma #{order_id}</b>\n\n"
        f"📊 Holat: <b>{status}</b>\n"
        f"📅 Sana: {str(order['created_at'])[:16]}\n\n"
        f"🛍 <b>Mahsulotlar:</b>\n{items_text}\n\n"
        f"💰 <b>Jami: {fmt_price(order['total_price'])} so'm</b>\n\n"
        f"📱 Telefon: {order['phone']}\n"
        f"📍 Manzil: {order['address']}\n"
        + (f"📝 Izoh: {order['note']}\n" if order['note'] else "")
    )

    try:
        await callback.message.edit_text(
            text, reply_markup=order_detail_kb(order_id), parse_mode="HTML"
        )
    except Exception:
        await callback.message.answer(
            text, reply_markup=order_detail_kb(order_id), parse_mode="HTML"
        )
    await callback.answer()
