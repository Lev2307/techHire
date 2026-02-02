from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api_handlers.handlers import get_applicant_info_by_telegram_id, edit_applicant_profile, get_applicant_auth_token
from keyboards.inline_keyboards import profile_inline_kbs, edit_profile_inline_kbs, login_inline_keyboard

profile_router = Router()

class FirstName(StatesGroup):
    first_name_input = State()

@profile_router.callback_query(F.data == 'profile')
async def profile_info(callback_query: CallbackQuery):
    applicant = await get_applicant_info_by_telegram_id(callback_query.from_user.id)
    email = f"Почта — <i>{applicant.get('email')}</i>" if applicant.get('email') else "<i>Почта не привязана</i>"
    sub_check = "Подписка оформлена ✅" if applicant.get('is_sub') else "Подписка отсутствует ❌"
    notifications_check = "Уведомления включены 🔔" if applicant.get('notifications_enabled') else "Уведомления отключены 🔕"
    work_formats = ", ".join([i["name"] for i in applicant.get('preferred_work_formats')])
    specializations_list = ", ".join([i["name"] for i in applicant.get('specializations')])
    technologies_list = ", ".join([i["name"] for i in applicant.get('technologies')])
    await callback_query.message.edit_text(
        f"Настройки⚙️\n\nИмя пользователя — <b>{applicant.get('first_name')}</b>\n{email}\n{sub_check}\n{notifications_check}\n\nГород — <i>{applicant.get('city')}</i>\nОпыт работы — <i>{applicant.get('experience')}</i>\n\nПредпочитаемые форматы работы: <i>{work_formats}</i>\nСпециализации: <i>{specializations_list}</i>\nТехнологии: <i>{technologies_list}</i>",
        parse_mode="HTML",
        reply_markup=profile_inline_kbs(),
    )

@profile_router.callback_query(F.data == "edit_profile_start_message")
async def edit_profile_start_message(callback_query: CallbackQuery):
    applicant_data = await get_applicant_info_by_telegram_id(callback_query.from_user.id)
    await callback_query.message.edit_text("Выберите поле для редактирования:", reply_markup=edit_profile_inline_kbs(applicant_data))

@profile_router.callback_query(F.data == 'edit-first_name')
async def edit_first_name(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Введите новое имя отображаемое имя пользователя')
    await state.set_state(FirstName.first_name_input)

@profile_router.message(FirstName.first_name_input)
async def process_editing_first_name(message: Message, state: FSMContext):
    data = {
        'first_name': message.text
    }
    auth_token = await get_applicant_auth_token(message.from_user.id)
    key = auth_token.get("auth_token")
    success, result = await edit_applicant_profile(data=data, token=key, user_id=message.from_user.id)
    if success:
        await message.answer(f"Вы успешно изменили имя пользователя! Теперь ваше отображаемое имя - <i>{result.get('first_name')}</i>", parse_mode="html", reply_markup=profile_inline_kbs())
    else:
        if result.get("error") == "unauthorized":
            await message.answer(
                "⚠️ <b>Сессия истекла</b>\nДля безопасности мы завершили ваш сеанс. Пожалуйста, авторизуйтесь заново.",
                parse_mode="html",
                reply_markup=login_inline_keyboard()
            )
        else:
            await message.answer("Упс! Что-то пошло не так при обновлении имени.", reply_markup=profile_inline_kbs())
    await state.clear()