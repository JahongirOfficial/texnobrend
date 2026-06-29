import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN, ADMIN_IDS, EFFECTS
from database import init_db
from handlers import main_router
from middleware import SubscriptionMiddleware


async def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger("texnobrend")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Subscription check middleware (applied to all messages & callbacks)
    dp.message.middleware(SubscriptionMiddleware())
    dp.callback_query.middleware(SubscriptionMiddleware())

    dp.include_router(main_router)

    # Global error handler to catch and handle all unhandled exceptions
    @dp.errors()
    async def global_error_handler(event):
        logger.error(f"Global error: {event.exception}", exc_info=True)
        try:
            if event.update.callback_query:
                await event.update.callback_query.answer(
                    "⚠️ Tizimda xatolik yuz berdi. Iltimos, keyinroq qayta urining.",
                    show_alert=True
                )
            elif event.update.message:
                await event.update.message.answer(
                    "⚠️ Tizimda xatolik yuz berdi. Iltimos, keyinroq qayta urining."
                )
        except Exception:
            pass

    logger.info("Initializing database...")
    await init_db()
    logger.info("Database ready.")


    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                "🟢 <b>Texnobrend Bot ishga tushdi!</b>\n\n"
                "<pre>"
                "┌─────────────────────────────────┐\n"
                "│ ✅ SQLite + 59 mahsulot          │\n"
                "│ ✅ Brand→Kategoriya→Model         │\n"
                "│ ✅ Mahsulot rasmlari              │\n"
                "│ ✅ Majburiy obuna middleware       │\n"
                "│ ✅ Support / Manzil / Kalkulyator │\n"
                "│ ✅ ButtonStyle danger/success ✓   │\n"
                "│ ✅ CopyTextButton (API 7.11)      │\n"
                "│ ✅ Message Effects (API 7.4)      │\n"
                "│ ✅ Premium Stiker tizimi          │\n"
                "│ ✅ Admin panel: broadcast+orders  │\n"
                "└─────────────────────────────────┘"
                "</pre>\n\n"
                f"⏰ Vaqt: <code>{now}</code>\n"
                f"🔑 Admin panel: /panel",
                message_effect_id=EFFECTS["confetti"],
            )
        except Exception as e:
            logger.warning(f"Admin notify failed ({admin_id}): {e}")

    logger.info("Bot polling started. Press Ctrl+C to stop.")
    await dp.start_polling(bot, skip_updates=True, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    asyncio.run(main())
