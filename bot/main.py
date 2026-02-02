import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from handlers.profile import profile_router
from handlers.start import start_router
from db.database import create_connection

async def main():
    dp_connection = create_connection()
    session = AiohttpSession(proxy=os.environ.get('PROXY'))
    bot = Bot(token=os.environ.get('TELEGRAM_BOT_TOKEN'), session=session)
    dp = Dispatcher()
    dp["conn"] = dp_connection

    dp.include_routers(start_router, profile_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())