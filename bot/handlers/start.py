import os

from aiogram import Router, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command

import httpx

from db.database import get_applicant_telegram, activate_applicant_linked_telegram

start_router = Router()

async def get_applicant_info(tg_id: int):
    async with httpx.AsyncClient() as client:
        try:
            # Используем имя сервиса 'backend' из docker-compose
            response = await client.get(f"http://backend:8000/api/accounts/by-telegram/{tg_id}", headers={"X-Internal-Token": os.environ.get("TELEGRAM_BOT_TOKEN")})
            if response.status_code == 200:
                applicant_data = response.json()
                return applicant_data
        except Exception as e:
            print(f"Ошибка связи с API: {e}")

@start_router.message(Command('start'))
async def start(message: Message, dispatcher: Dispatcher):
    connection_to_db = dispatcher["conn"]
    applicant_telegram = get_applicant_telegram(connection_to_db, message.from_user.id)
    if applicant_telegram:
        applicant = await get_applicant_info(message.from_user.id) # модель Applicant, хочу сделать запросом к своему api
        print(applicant)
        if applicant_telegram[-1] == False: # тг не привязано
            activate_applicant_linked_telegram(connection_to_db, message.from_user.id, message.chat.id)
            await message.answer(f'Вы успешно активировали! Добро пожаловать')
        else: # Пользователь уже привязал тг
            await message.answer(f'Добро пожаловать в систему')
    else:
        await message.answer('Брад, ты ещё не создал аккаунт в сервисе TechHire!')