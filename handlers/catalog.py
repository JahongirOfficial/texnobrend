from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.fsm.context import FSMContext

import database as db
from keyboards import (
    brands_kb, categories_kb, products_kb, product_detail_kb,
    main_menu_kb, cancel_kb,
)
from utils import make_product_text
from states import Search
from config import ITEMS_PER_PAGE

router = Router()


async def edit_or_reply(callback: CallbackQuery, text: str, reply_markup=None):
    try:
        await callback.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
    except Exception:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


# ──────────────── catalog entry ────────────────

@router.message(F.text == "🛒 Mahsulotlar")
async def menu_catalog(message: Message, state: FSMContext):
    await state.clear()
    brands = await db.get_brands()
    if brands:
        await message.answer(
            "🏷 <b>Brendni tanlang:</b>",
            reply_markup=brands_kb(brands),
            parse_mode="HTML",
        )
    else:
        cats = await db.get_categories()
        await message.answer(
            "📂 <b>Kategoriyani tanlang:</b>",
            reply_markup=categories_kb(cats),
            parse_mode="HTML",
        )


@router.callback_query(F.data == "all_categories")
async def cb_all_categories(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    brands = await db.get_brands()
    if brands:
        await edit_or_reply(
            callback,
            "🏷 <b>Brendni tanlang:</b>",
            reply_markup=brands_kb(brands),
        )
    else:
        cats = await db.get_categories()
        await edit_or_reply(
            callback,
            "📂 <b>Kategoriyani tanlang:</b>",
            reply_markup=categories_kb(cats),
        )
    await callback.answer()


# ──────────────── brand → categories ────────────────

@router.callback_query(F.data.startswith("brand:"))
async def cb_brand(callback: CallbackQuery):
    brand = callback.data.split(":", 1)[1]
    cats = await db.get_categories_by_brand(brand)
    await edit_or_reply(
        callback,
        f"🏷 <b>{brand}</b> — Kategoriya tanlang:",
        reply_markup=categories_kb(cats, brand=brand),
    )
    await callback.answer()


# ──────────────── category → products ────────────────

@router.callback_query(F.data.startswith("cat:"))
async def cb_category(callback: CallbackQuery):
    _, cat_id, page = callback.data.split(":")
    cat_id, page = int(cat_id), int(page)
    cat = await db.get_category(cat_id)
    products, total = await db.get_products(cat_id, page, ITEMS_PER_PAGE)

    if not products:
        await callback.answer("Bu kategoriyada mahsulot yo'q", show_alert=True)
        return

    cat_name = cat["name"] if cat else "Kategoriya"
    brand = cat["brand"] if cat else ""
    title = f"{brand} · {cat_name}" if brand else cat_name

    await edit_or_reply(
        callback,
        f"📦 <b>{title}</b>\n"
        f"<i>Jami: {total} ta mahsulot</i>",
        reply_markup=products_kb(products, cat_id, page, total, ITEMS_PER_PAGE, brand=brand),
    )
    await callback.answer()




# ──────────────── product detail ────────────────

@router.callback_query(F.data.startswith("prod:"))
async def cb_product(callback: CallbackQuery):
    import json
    product_id = int(callback.data.split(":")[1])
    product = await db.get_product(product_id)

    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return

    try:
        text = make_product_text(product)
    except Exception as e:
        await callback.answer(f"Xatolik: {e}", show_alert=True)
        return

    # Option selection initialization (temporarily disabled as per user request)
    opts = {}
    product_dict = dict(product)
    # if product_dict.get("options"):
    #     try:
    #         opts = json.loads(product_dict["options"])
    #     except Exception:
    #         pass

    current_sel = None
    if opts:
        current_sel = [0] * len(opts)
        selected_labels = []
        keys = list(opts.keys())
        for idx, key in enumerate(keys):
            vals = opts[key]
            selected_labels.append(f"{key.capitalize()}: <b>{vals[0]}</b>")
        options_text = "⚙️ <b>Tanlangan xususiyatlar:</b>\n" + "\n".join(f"  • {lbl}" for lbl in selected_labels)
        text += f"\n\n{options_text}"

    cat_id = product["category_id"]
    kb = product_detail_kb(
        product_id,
        cat_id,
        added=False,
        options_json=product_dict.get("options"),
        current_sel=current_sel
    )
    image = product["image_file_id"]

    await callback.answer()

    if image:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=image,
            caption=text,
            reply_markup=kb,
            parse_mode="HTML",
        )
    else:
        try:
            await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")


@router.callback_query(F.data.startswith("opt_change:"))
async def cb_opt_change(callback: CallbackQuery):
    import json
    _, product_id, attr_idx, new_indices_str = callback.data.split(":")
    product_id = int(product_id)
    current_sel = [int(x) for x in new_indices_str.split("_")]
    
    product = await db.get_product(product_id)
    if not product:
        await callback.answer("Mahsulot topilmadi", show_alert=True)
        return
        
    text = make_product_text(product)
    
    opts = {}
    product_dict = dict(product)
    # if product_dict.get("options"):
    #     try:
    #         opts = json.loads(product_dict["options"])
    #     except Exception:
    #         pass
            
    if opts:
        selected_labels = []
        keys = list(opts.keys())
        for idx, key in enumerate(keys):
            vals = opts[key]
            val_idx = current_sel[idx] if idx < len(current_sel) else 0
            selected_labels.append(f"{key.capitalize()}: <b>{vals[val_idx]}</b>")
        options_text = "⚙️ <b>Tanlangan xususiyatlar:</b>\n" + "\n".join(f"  • {lbl}" for lbl in selected_labels)
        text += f"\n\n{options_text}"
        
    kb = product_detail_kb(
        product_id,
        product["category_id"],
        added=False,
        options_json=product["options"],
        current_sel=current_sel
    )
    
    await callback.answer()
    
    if product["image_file_id"]:
        try:
            await callback.message.edit_caption(caption=text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass
    else:
        try:
            await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="HTML")
        except Exception:
            pass



# ──────────────── search ────────────────

@router.message(F.text == "🔍 Qidirish")
async def menu_search(message: Message, state: FSMContext):
    await state.set_state(Search.query)
    await message.answer(
        "🔍 <b>Mahsulot qidirish</b>\n\nQidirmoqchi bo'lgan mahsulotingiz nomini yoki modelini yozing:",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )


@router.callback_query(F.data == "search")
async def cb_search(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Search.query)
    await callback.message.answer(
        "🔍 <b>Mahsulot qidirish</b>\n\nQidirmoqchi bo'lgan mahsulotingiz nomini yoki modelini yozing:",
        reply_markup=cancel_kb(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.message(Search.query, F.text)
async def do_search(message: Message, state: FSMContext):
    if message.text == "❌ Bekor qilish":
        await state.clear()
        await message.answer("❌ Qidiruv bekor qilindi.", reply_markup=main_menu_kb())
        return


    query = message.text.strip()
    if len(query) < 2:
        await message.answer("⚠️ Iltimos, qidiruv aniqroq bo'lishi uchun kamida 2 ta harf kiriting!")
        return

    # Show loading indicator
    loading = await message.answer("🔍 Mahsulotlar katalogidan qidirilmoqda, iltimos ozgina kuting...")

    results = await db.search_products(query, limit=5)
    await state.clear()

    try:
        await loading.delete()
    except Exception:
        pass

    if not results:
        await message.answer(
            f"😔 Afsuski, <b>«{query}»</b> so'rovi bo'yicha birorta ham mahsulot topilmadi.\n\n"
            "💡 <b>Maslahat:</b> Brend yoki mahsulot turini yozib ko'ring.\n"
            "<i>Masalan: Samsung, iPhone, noutbuk, televizor...</i>",
            reply_markup=main_menu_kb(),
            parse_mode="HTML",
        )
        return

    builder = InlineKeyboardBuilder()
    for i, p in enumerate(results, 1):
        price_str = f"{p['price']:,}".replace(",", " ")
        stock_icon = "✅" if p["stock"] > 0 else "❌"
        builder.button(
            text=f"{i}. {stock_icon} {p['name']} — {price_str} so'm",
            callback_data=f"prod:{p['id']}",
        )
    builder.adjust(1)
    builder.row(
        InlineKeyboardButton(text="🔍 Qayta qidirish", callback_data="search"),
        InlineKeyboardButton(text="🏠 Bosh menyu", callback_data="main_menu"),
    )

    await message.answer(
        f"🔍 <b>«{query}»</b> so'rovingiz bo'yicha topilgan natijalar (eng mos {len(results)} ta):\n\n"
        f"👇 Tafsilotlarni ko'rish uchun kerakli mahsulot ustiga bosing:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML",
    )


@router.message(Search.query)
async def do_search_invalid(message: Message):
    await message.answer("⚠️ Iltimos, qidirmoqchi bo'lgan mahsulot nomini matn ko'rinishida yozib yuboring!")

