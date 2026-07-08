from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiohttp import web

from bot.config import load_settings
from bot.database import Database
from bot.handlers import admin, user
from bot.services.courses import CourseService
from bot.web import create_app


async def main() -> None:
    settings = load_settings()
    if not settings.bot_token:
        raise RuntimeError("BOT_TOKEN is required. Copy .env.example to .env and fill it.")

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    db = Database(settings.sqlite_path)
    await db.init()
    courses = CourseService(settings.courses_path)

    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(db=db, settings=settings, courses=courses)
    dp.include_router(admin.router)
    dp.include_router(user.router)

    await bot.delete_webhook(drop_pending_updates=True)

    web_app = create_app(db, settings, bot)
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    logging.info("Lead API is listening on http://%s:%s", settings.web_host, settings.web_port)

    try:
        await dp.start_polling(bot)
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
