import time
from typing import Union

from aiogram import Router, F, Dispatcher
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext

from api_handlers.handlers import login, logout, get_applicant_auth_token
from keyboards.inline_keyboards import login_inline_kbs, failed_login_inline_kbs, start_inline_kbs
from utils.factories import generate_telegram_oauth_hash

auth_router = Router()

async def handle_api_unauthorized_error(event: Union[CallbackQuery, Message], result: dict):
    """Централизованная обработка ошибки авторизации 401 API для всех хендлеров профиля"""
    if result.get("error") == "unauthorized":
        error_text = "⚠️ <b>Сессия истекла</b>\nДля безопасности мы завершили ваш сеанс. Пожалуйста, авторизуйтесь заново."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(
                error_text,
                parse_mode="html",
                reply_markup=login_inline_kbs()
            )
            await event.answer()
        elif isinstance(event, Message):
            await event.edit_text(
                error_text,
                parse_mode="html",
                reply_markup=login_inline_kbs()
            )
        return True
    return False

@auth_router.callback_query(F.data == 're-authorization')
async def re_authorization(callback_query: CallbackQuery, dispatcher: Dispatcher):
    # data - id, username, first_name, hash, auth_date
    auth_data = {
        'id': callback_query.from_user.id,
        'username': callback_query.from_user.username,
        'first_name': callback_query.from_user.first_name,
        'auth_date': int(time.time())
    }
    auth_hash = generate_telegram_oauth_hash(data=auth_data, bot_token=dispatcher["telegram_bot_token"])
    auth_data['hash'] = auth_hash

    successful_login, _ = await login(data=auth_data)
    if successful_login:
        await callback_query.message.edit_text('✅ <b>Авторизация успешна!</b>\nВаша сессия обновлена.\nТеперь вы можете продолжить пользоваться функционалом бота!', reply_markup=start_inline_kbs(), parse_mode="html")
    else:
        await callback_query.message.edit_text("Что-то пошло не так при попытке авторизации в сервисе Techhire! Попробуйте позднее...", reply_markup=failed_login_inline_kbs())

@auth_router.callback_query(F.data == "logout")
async def logout_handler(callback_query: CallbackQuery, state: FSMContext):
    auth_token = await get_applicant_auth_token(callback_query.from_user.id)
    logout_success, _ = await logout(token_key=auth_token)
    if logout_success:
        await callback_query.message.edit_text("🚪 " + _["message"])
    await state.clear()