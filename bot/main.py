import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession

from db.database import create_connection
from handlers.auth import auth_router
from handlers.profile import profile_router
from handlers.start import start_router
from handlers.favourites import favourites_router

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
PROXY_URL = os.environ.get('PROXY')

async def main():
    dp_connection = create_connection()
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=TOKEN, session=session)
    dp = Dispatcher()
    dp["conn"] = dp_connection
    dp["telegram_bot_token"] = TOKEN

    dp.include_routers(auth_router, profile_router, favourites_router, start_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())