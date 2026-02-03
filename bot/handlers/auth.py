from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

auth_router = Router()

@auth_router.callback_query(F.data == 're-authorization')
async def re_authorization(callback_query: CallbackQuery):
    await callback_query.message.edit_text('Происходит авторизация ------!-!_!')