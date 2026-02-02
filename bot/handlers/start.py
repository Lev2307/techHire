from aiogram import Router, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from db.database import get_applicant_telegram, activate_applicant_linked_telegram
from keyboards.inline_keyboards import start_inline_kbs

start_router = Router()

@start_router.message(Command('start'))
async def start(message: Message, dispatcher: Dispatcher):
    connection_to_db = dispatcher["conn"]
    applicant_telegram = get_applicant_telegram(connection_to_db, message.from_user.id)
    if applicant_telegram:
        if applicant_telegram[-1] == False: # тг не привязано
            activate_applicant_linked_telegram(connection_to_db, message.from_user.id, message.chat.id)
            await message.answer(f'Вы успешно привязали телеграм-бота к аккаунту Techhire! Я - TechHire бот🤖. Чем могу помочь?', reply_markup=start_inline_kbs())
        else: # Пользователь уже привязал тг
            await message.answer(f'🏠 Главное меню', reply_markup=start_inline_kbs())
    else:
        await message.answer('Брад, ты ещё не создал аккаунт в сервисе TechHire!')

@start_router.callback_query(F.data == 'go_to_start')
async def go_to_start(callback_query: CallbackQuery):
    await callback_query.answer("Вы вернулись на главную!")
    await callback_query.message.delete()
    await callback_query.message.answer(f'🏠 Главное меню', reply_markup=start_inline_kbs())