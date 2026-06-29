from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import (
    cart_kb, cart_item_kb, checkout_phone_kb, checkout_confirm_kb,
    payment_kb, main_menu_kb, remove_kb, cancel_kb,
)
from utils import fmt_price, send_sticker, send_with_effect
from states import Checkout
from config import ADMIN_IDS

router = Router()


async def _show_cart(target, user_id: int):
    items = await db.cart_get(user_id)
    if not items:
        text = "🛍 <b>Savatingiz bo'sh</b>\n\nMahsulotlar bo'limidan qo'shing."
        kb = cart_kb(has_items=False)
    else:
        total = sum(i["price"] * i["quantity"] for i in items)
        lines = ["🛍 <b>Sizning savatchangiz:</b>\n"]
        for i in items:
            name = f"{i['name']} ({i['selected_options']})" if i["selected_options"] else i["name"]
            lines.append(
                f"• {name}\n"
                f"  {fmt_price(i['price'])} × {i['quantity']} = "
                f"<b>{fmt_price(i['price'] * i['quantity'])} so'm</b>"
            )
        lines.append(f"\n💰 <b>Jami: {fmt_price(total)} so'm</b>")
        text = "\n".join(lines)
        kb = cart_kb(has_items=True, items=items)

    if isinstance(target, Message):
        await target.answer(text, reply_markup=kb, parse_mode="HTML")
    else:
        try:
            await target.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await target.message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.message(F.text == "🛍 Savatcha")
async def menu_cart(message: Message):
    await _show_cart(message, message.from_user.id)


@router.callback_query(F.data == "cart")
async def cb_cart(callback: CallbackQuery):
    await _show_cart(callback, callback.from_user.id)
    await callback.answer()



# ──────────────── add to cart ────────────────

@router.callback_query(F.data.startswith("cart_add:"))
async def cb_cart_add(callback: CallbackQuery):
    import json
    parts = callback.data.split(":")
    product_id = int(parts[1])
    indices_str = parts[2] if len(parts) > 2 else ""

    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return
    product_dict = dict(product)
    if not product_dict["stock"]:
        await callback.answer("❌ Bu mahsulot mavjud emas", show_alert=True)
        return

    # Parse and format option selections
    selected_opts_label = ""
    current_sel = None
    if indices_str and product_dict.get("options"):
        try:
            opts = json.loads(product_dict["options"])
            current_sel = [int(x) for x in indices_str.split("_")]
            selected_labels = []
            keys = list(opts.keys())
            for idx, key in enumerate(keys):
                vals = opts[key]
                val_idx = current_sel[idx] if idx < len(current_sel) else 0
                selected_labels.append(vals[val_idx])
            selected_opts_label = ", ".join(selected_labels)
        except Exception:
            pass

    # Check stock limits
    cart_items = await db.cart_get(callback.from_user.id)
    current_qty = 0
    for item in cart_items:
        if item["product_id"] == product_id and item["selected_options"] == selected_opts_label:
            current_qty = item["quantity"]
            break

    if current_qty + 1 > product_dict["stock"]:
        await callback.answer(
            f"❌ Omborda atigi {product_dict['stock']} ta mahsulot bor! Savatchangizga ko'proq qo'shib bo'lmaydi.",
            show_alert=True
        )
        return

    await db.cart_add(callback.from_user.id, product_id, selected_opts_label)
    
    # Dynamically change the button state to "✅ Savatga qo'shildi" (blue)
    cat_id = product_dict["category_id"]
    from keyboards import product_detail_kb
    import asyncio
    
    try:
        await callback.message.edit_reply_markup(
            reply_markup=product_detail_kb(product_id, cat_id, added=True, options_json=product_dict.get("options"), current_sel=current_sel)
        )
    except Exception:
        pass
    
    await callback.answer()
    
    # Wait 1 second
    await asyncio.sleep(1)
    
    # Restore the button state back to "🛒 Savatga qo'shish" (green)
    try:
        await callback.message.edit_reply_markup(
            reply_markup=product_detail_kb(product_id, cat_id, added=False, options_json=product_dict.get("options"), current_sel=current_sel)
        )
    except Exception:
        pass



# ──────────────── fast order ────────────────

@router.callback_query(F.data.startswith("fast_order:"))
async def cb_fast_order(callback: CallbackQuery, state: FSMContext):
    import json
    parts = callback.data.split(":")
    product_id = int(parts[1])
    indices_str = parts[2] if len(parts) > 2 else ""

    product = await db.get_product(product_id)
    if not product:
        await callback.answer("❌ Mahsulot mavjud emas", show_alert=True)
        return
    product_dict = dict(product)
    if not product_dict["stock"]:
        await callback.answer("❌ Mahsulot mavjud emas", show_alert=True)
        return

    # Parse options
    selected_opts_label = ""
    if indices_str and product_dict.get("options"):
        try:
            opts = json.loads(product_dict["options"])
            current_sel = [int(x) for x in indices_str.split("_")]
            selected_labels = []
            keys = list(opts.keys())
            for idx, key in enumerate(keys):
                vals = opts[key]
                val_idx = current_sel[idx] if idx < len(current_sel) else 0
                selected_labels.append(vals[val_idx])
            selected_opts_label = ", ".join(selected_labels)
        except Exception:
            pass

    await db.cart_clear(callback.from_user.id)
    await db.cart_add(callback.from_user.id, product_id, selected_opts_label)
    await callback.answer("⚡ Tez buyurtma!")
    await state.set_state(Checkout.phone)
    await callback.message.answer(
        "📱 <b>Tez buyurtma</b>\n\n"
        "Telefon raqamingizni yuboring yoki kiriting:",
        reply_markup=checkout_phone_kb(),
        parse_mode="HTML",
    )



# ──────────────── cart actions ────────────────

@router.callback_query(F.data.startswith("cart_remove:"))
async def cb_cart_remove(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    await db.cart_remove_by_id(callback.from_user.id, cart_id)
    await callback.answer("🗑 O'chirildi")
    await _show_cart(callback, callback.from_user.id)


@router.callback_query(F.data == "cart_clear")
async def cb_cart_clear(callback: CallbackQuery):
    await db.cart_clear(callback.from_user.id)
    await callback.answer("🗑 Savat tozalandi")
    await _show_cart(callback, callback.from_user.id)


@router.callback_query(F.data.startswith("qty_inc:"))
async def cb_qty_inc(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    items = await db.cart_get(callback.from_user.id)
    item = next((i for i in items if i["id"] == cart_id), None)
    if item:
        new_qty = item["quantity"] + 1
        if new_qty > item["stock"]:
            await callback.answer(
                f"❌ Omborda atigi {item['stock']} ta mahsulot bor! Savatchangizga ko'proq qo'shib bo'lmaydi.",
                show_alert=True
            )
            return
        await db.cart_set_qty_by_id(callback.from_user.id, cart_id, new_qty)
        await _show_cart(callback, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data.startswith("qty_dec:"))
async def cb_qty_dec(callback: CallbackQuery):
    cart_id = int(callback.data.split(":")[1])
    items = await db.cart_get(callback.from_user.id)
    item = next((i for i in items if i["id"] == cart_id), None)
    if item:
        new_qty = item["quantity"] - 1
        if new_qty <= 0:
            await db.cart_remove_by_id(callback.from_user.id, cart_id)
            await callback.answer("🗑 Mahsulot olib tashlandi")
        else:
            await db.cart_set_qty_by_id(callback.from_user.id, cart_id, new_qty)
        await _show_cart(callback, callback.from_user.id)
    await callback.answer()



# ──────────────── checkout FSM ────────────────

@router.callback_query(F.data == "checkout")
async def cb_checkout(callback: CallbackQuery, state: FSMContext):
    items = await db.cart_get(callback.from_user.id)
    if not items:
        await callback.answer("Savatchangiz bo'sh!", show_alert=True)
        return

    # Check stock for all items
    for item in items:
        if item["quantity"] > item["stock"]:
            await callback.answer(
                f"❌ «{item['name']}» mahsulotidan omborda yetarli emas (omborda: {item['stock']} ta). "
                f"Iltimos, miqdorini kamaytiring!",
                show_alert=True
            )
            return

    await state.set_state(Checkout.phone)
    await callback.message.answer(
        "📦 <b>Buyurtma rasmiylashtirish</b>\n\n"
        "1️⃣ Telefon raqamingizni yuboring:",
        reply_markup=checkout_phone_kb(),
        parse_mode="HTML",
    )
    await callback.answer()



@router.message(Checkout.phone)
async def checkout_phone(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    if message.contact:
        phone = message.contact.phone_number
    elif message.text and (message.text.startswith("+") or message.text.isdigit()):
        phone = message.text.strip()
    else:
        await message.answer("❌ Iltimos, telefon raqamingizni yuboring yoki kiriting:")
        return

    await state.update_data(phone=phone)
    await db.update_user_phone(message.from_user.id, phone)
    await state.set_state(Checkout.address)
    await message.answer(
        "2️⃣ Yetkazib berish manzilingizni kiriting:\n"
        "<i>Misol: Toshkent sh., Yunusobod tumani, Amir Temur ko'chasi 10-uy</i>",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(Checkout.address, F.text)
async def checkout_address(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return

    await state.update_data(address=message.text.strip())
    await state.set_state(Checkout.note)
    await message.answer(
        "3️⃣ Qo'shimcha izoh (ixtiyoriy):\n"
        "<i>Maxsus xohish, rang, model va h.k yoki «Yo'q» deb yozing</i>",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.message(Checkout.address)
async def checkout_address_invalid(message: Message):
    await message.answer("❌ Iltimos, manzilni matn ko'rinishida yozing!")


@router.message(Checkout.note, F.text)
async def checkout_note(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Bekor qilindi.", reply_markup=main_menu_kb())
        return


    note = "" if message.text.strip().lower() in ("yo'q", "yoq", "-", "none", "") else message.text.strip()
    await state.update_data(note=note)
    await state.set_state(Checkout.confirm)

    data = await state.get_data()
    items = await db.cart_get(message.from_user.id)
    total = sum(i["price"] * i["quantity"] for i in items)

    items_text = "\n".join(
        f"  • {i['name']} × {i['quantity']} = {fmt_price(i['price'] * i['quantity'])} so'm"
        for i in items
    )

    await message.answer(
        f"📋 <b>Buyurtmangizni tasdiqlang:</b>\n\n"
        f"🛍 <b>Mahsulotlar:</b>\n{items_text}\n\n"
        f"💰 <b>Jami: {fmt_price(total)} so'm</b>\n\n"
        f"📱 Telefon: <b>{data['phone']}</b>\n"
        f"📍 Manzil: <b>{data['address']}</b>\n"
        + (f"📝 Izoh: <b>{note}</b>\n" if note else ""),
        reply_markup=checkout_confirm_kb(),
        parse_mode="HTML",
    )
@router.message(Checkout.note)
async def checkout_note_invalid(message: Message):
    await message.answer("❌ Iltimos, izohni matn ko'rinishida yozing!")



@router.callback_query(Checkout.confirm, F.data == "order_confirm")
async def order_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = callback.from_user.id

    items = await db.cart_get(user_id)
    if not items:
        await callback.answer("Savatchangiz bo'sh!", show_alert=True)
        return

    # Check stock for all items
    for item in items:
        if item["quantity"] > item["stock"]:
            await callback.answer(
                f"❌ «{item['name']}» mahsulotidan omborda yetarli emas (omborda: {item['stock']} ta). "
                f"Iltimos, miqdorini kamaytiring!",
                show_alert=True
            )
            return

    order_id = await db.create_order(user_id, data["phone"], data["address"], data.get("note", ""))
    await state.clear()

    if not order_id:
        await callback.answer("Xatolik yuz berdi!", show_alert=True)
        return


    await callback.message.delete()
    bot = callback.bot

    await send_sticker(bot, callback.message.chat.id, "success")
    await send_with_effect(
        bot, callback.message.chat.id,
        f"🎉 <b>Buyurtmangiz qabul qilindi!</b>\n\n"
        f"📋 Buyurtma raqami: <b>#{order_id}</b>\n\n"
        f"⏳ Tez orada admin siz bilan bog'lanadi.\n"
        f"📦 Buyurtma holati: <b>Kutmoqda</b>\n\n"
        f"To'lov usulini tanlang:",
        effect_key="fireworks",
        reply_markup=payment_kb(order_id),
    )
    await callback.answer("✅ Buyurtma qabul qilindi!")

    # Notify admins
    order, items = await db.get_order(order_id)
    user = callback.from_user
    items_text = "\n".join(f"• {i['name']} x{i['quantity']} — {fmt_price(i['price'])} so'm" for i in items)
    notify_text = (
        f"🛎 <b>Yangi buyurtma #{order_id}!</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}"
        + (f" (@{user.username})" if user.username else "") + "\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"📱 Tel: {data['phone']}\n"
        f"📍 Manzil: {data['address']}\n"
        + (f"📝 Izoh: {data.get('note', '')}\n" if data.get('note') else "")
        + f"\n🛍 Mahsulotlar:\n{items_text}\n\n"
        f"💰 Jami: <b>{fmt_price(order['total_price'])} so'm</b>"
    )
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, notify_text, parse_mode="HTML")
        except Exception:
            pass


@router.callback_query(Checkout.confirm, F.data == "order_cancel")
async def order_cancel(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("❌ Buyurtma bekor qilindi.", reply_markup=main_menu_kb())
    await callback.answer()


@router.callback_query(Checkout.confirm, F.data == "order_edit")
async def order_edit(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Checkout.phone)
    await callback.message.answer(
        "📱 Yangi telefon raqamingizni yuboring:",
        reply_markup=checkout_phone_kb(),
    )
    await callback.answer()


# ──────────────── payments integration ────────────────

@router.callback_query(F.data.startswith("pay_click:") | F.data.startswith("pay_payme:"))
async def pay_invoice(callback: CallbackQuery):
    from config import CLICK_PROVIDER_TOKEN, PAYME_PROVIDER_TOKEN
    from aiogram.types import LabeledPrice
    
    parts = callback.data.split(":")
    provider = parts[0]
    order_id = int(parts[1])
    
    if provider == "pay_click":
        token = CLICK_PROVIDER_TOKEN
        prov_label = "Click"
    else:
        token = PAYME_PROVIDER_TOKEN
        prov_label = "Payme"
        
    if not token:
        await callback.answer(f"⚠️ {prov_label} to'lov tizimi sozlanmagan. Naqd to'lashdan foydalaning.", show_alert=True)
        return
        
    order, items = await db.get_order(order_id)
    if not order:
        await callback.answer("❌ Buyurtma topilmadi!", show_alert=True)
        return
        
    if order["status"] != "pending":
        await callback.answer("⚠️ Ushbu buyurtma to'lanib bo'lgan yoki bekor qilingan.", show_alert=True)
        return
        
    await callback.answer()
    
    total_price = order["total_price"]
    prices = [
        LabeledPrice(label=f"Buyurtma #{order_id}", amount=total_price * 100)
    ]
    
    try:
        await callback.message.answer_invoice(
            title=f"Buyurtma #{order_id}",
            description=f"Texnobrend do'konidan xarid (To'lov tizimi: {prov_label})",
            payload=f"order_id:{order_id}",
            provider_token=token,
            currency="UZS",
            prices=prices,
            start_parameter=f"pay-order-{order_id}"
        )
    except Exception as e:
        await callback.message.answer(f"❌ Invoys yaratishda xatolik yuz berdi: {e}")


# ──────────────── pre-checkout & successful payment ────────────────

from aiogram.types import PreCheckoutQuery

@router.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_query: PreCheckoutQuery, bot: Bot):
    try:
        await bot.answer_pre_checkout_query(pre_checkout_query_id=pre_checkout_query.id, ok=True)
    except Exception as e:
        import logging
        logging.error(f"Error in pre_checkout_query: {e}", exc_info=True)


@router.message(F.successful_payment)
async def on_successful_payment(message: Message):
    payload = message.successful_payment.invoice_payload
    try:
        order_id = int(payload.split(":")[1])
        await db.update_order_status(order_id, "processing")
        
        await message.answer(
            f"🎉 <b>To'lov muvaffaqiyatli amalga oshirildi!</b>\n\n"
            f"Sizning buyurtmangiz #{order_id} <b>Jarayonda</b> holatiga o'tkazildi. Tez orada kuryer bog'lanadi.",
            parse_mode="HTML",
            reply_markup=main_menu_kb()
        )
        
        # Notify admins
        from config import ADMIN_IDS
        for admin_id in ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"💳 <b>Buyurtma #{order_id} to'landi!</b>\n\n"
                    f"Foydalanuvchi: {message.from_user.full_name}\n"
                    f"To'langan summa: {fmt_price(message.successful_payment.total_amount // 100)} so'm",
                    parse_mode="HTML"
                )
            except Exception:
                pass
    except Exception as e:
        await message.answer(f"⚠️ To'lov hisobga olindi, ammo holatni yangilashda xatolik yuz berdi: {e}")


@router.callback_query(F.data.startswith("pay_cash:"))
async def pay_cash(callback: CallbackQuery):
    await callback.answer("✅ Naqd to'lash tanlandi. Yetkazib beruvchi siz bilan bog'lanadi.", show_alert=True)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(
        "💵 <b>Naqd to'lash</b>\n\nYetkazib beruvchi siz bilan bog'langanda to'lashingiz mumkin. Rahmat!",
        reply_markup=main_menu_kb(),
        parse_mode="HTML",
    )

