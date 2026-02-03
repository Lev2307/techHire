from typing import Union

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from api_handlers.handlers import (
    get_applicant_info_by_telegram_id, 
    edit_applicant_profile, 
    get_applicant_auth_token, 
    get_all_available_cities_with_applicant_option, 
    get_all_available_experience_choices_with_applicant_option,
    get_all_available_work_formats_with_applicant_options, 
    get_all_applicant_selected_work_formats_ids,
    get_all_available_specializations_with_applicant_options,
    get_all_applicant_selected_specializations_ids, 
    toggle_specialization_name,
    get_technologies_by_query,
    toggle_technology_name,
    get_all_applicant_selected_technologies_ids
)
from keyboards.inline_keyboards import (
    login_inline_kbs,
    profile_inline_kbs, 
    edit_profile_inline_kbs, 
    edit_city_inline_kbs, 
    edit_experience_inline_kbs, 
    edit_work_formats_inline_kbs, 
    edit_specializations_inline_kbs, 
    go_back_to_editing_profile_inline_kbs,
    edit_applicant_technologies_inline_kbs,
    go_back_to_editing_profile_or_stop_search_inline_kbs
)

profile_router = Router()

class FirstNameState(StatesGroup):
    typing_first_name = State()

class TechnologyState(StatesGroup):
    typing_tech = State()

async def handle_api_unauthorized_error(event: Union[CallbackQuery, Message], result):
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

@profile_router.callback_query(F.data == 'profile')
async def profile_info(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    auth_token = await get_applicant_auth_token(user_id)
    success, applicant_data = await get_applicant_info_by_telegram_id(token_key=auth_token, user_id=user_id)
    if success:
        email = f"Почта — <i>{applicant_data.get('email')}</i>" if applicant_data.get('email') else "<i>Почта не привязана</i>"
        sub_check = "Подписка оформлена ✅" if applicant_data.get('is_sub') else "Подписка отсутствует ❌"
        notifications_check = "Уведомления включены 🔔" if applicant_data.get('notifications_enabled') else "Уведомления отключены 🔕"
        work_formats = ", ".join([i["name"] for i in applicant_data.get('preferred_work_formats')])
        specializations_list = ", ".join([i["name"] for i in applicant_data.get('specializations')])
        technologies_list = ", ".join([i["name"] for i in applicant_data.get('technologies')])
        await callback_query.message.edit_text(
            f"Настройки⚙️\n\nИмя пользователя — <b>{applicant_data.get('first_name')}</b>\n{email}\n{sub_check}\n{notifications_check}\n\nГород — <i>{applicant_data.get('city')}</i>\nОпыт работы — <i>{applicant_data.get('experience')}</i>\n\nПредпочитаемые форматы работы: <i>{work_formats}</i>\nСпециализации: <i>{specializations_list}</i>\nТехнологии: <i>{technologies_list}</i>",
            parse_mode="HTML",
            reply_markup=profile_inline_kbs(),
        )
    else:
        if await handle_api_unauthorized_error(callback_query, applicant_data):
            return
        await callback_query.message.edit_text('Произошла непредвиденная ошибка. Пожалуйста, повторите запрос позже')


@profile_router.callback_query(F.data == "edit_profile_start_message")
async def edit_profile_start_message(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    auth_token = await get_applicant_auth_token(user_id)
    success, applicant_data = await get_applicant_info_by_telegram_id(token_key=auth_token, user_id=user_id)
    if success:
        await callback_query.message.edit_text("Выберите поле для редактирования:", reply_markup=edit_profile_inline_kbs(applicant_data))
    else:
        if await handle_api_unauthorized_error(callback_query, applicant_data):
            return 
        await callback_query.message.edit_text('Произошла непредвиденная ошибка. Пожалуйста, повторите запрос позже')

@profile_router.callback_query(F.data == 'edit-first_name')
async def edit_first_name(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Введите новое имя отображаемое имя пользователя: ')
    await state.set_state(FirstNameState.typing_first_name)

@profile_router.message(FirstNameState.typing_first_name)
async def process_editing_first_name(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = {
        'first_name': message.text
    }

    auth_token = await get_applicant_auth_token(user_id)
    success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
    if success:
        await message.answer(f"Вы успешно изменили имя пользователя! Теперь ваше отображаемое имя - <i>{_.get('first_name')}</i>", parse_mode="html", reply_markup=profile_inline_kbs())
    else:
        if await handle_api_unauthorized_error(message, _):
            return
        await message.answer("Упс! Что-то пошло не так при обновлении имени.", reply_markup=go_back_to_editing_profile_inline_kbs())
    await state.clear()

@profile_router.callback_query(F.data == 'edit-city')
async def edit_applicant_city(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    auth_token = await get_applicant_auth_token(user_id)
    success, city_choices = await get_all_available_cities_with_applicant_option(token_key=auth_token, user_id=user_id)
    if success:
        await callback_query.message.edit_text('Выберите город: ', reply_markup=edit_city_inline_kbs(city_choices))
    else:
        if await handle_api_unauthorized_error(callback_query, city_choices):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении города.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data.startswith('toggle_city:'))
async def toggle_city_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    new_city_name, status = data[1], data[2]
    data = {
        'city': new_city_name
    }
    if status != "selected": # проверка, что нельзя редачить тот же город
        auth_token = await get_applicant_auth_token(user_id)
        success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
        if success:
            success_markup, cities = await get_all_available_cities_with_applicant_option(token_key=auth_token, user_id=user_id)
            await callback_query.message.edit_reply_markup(reply_markup=edit_city_inline_kbs(cities))
            await callback_query.answer(f"Город изменен на {new_city_name}")
        else:
            if await handle_api_unauthorized_error(callback_query, _):
                return 
            await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении города.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data == 'edit-experience')
async def edit_applicant_experience(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id

    auth_token = await get_applicant_auth_token(user_id)
    success, experience_choices = await get_all_available_experience_choices_with_applicant_option(token_key=auth_token, user_id=user_id)
    if success:
        await callback_query.message.edit_text('Выберите опыт работы: ', reply_markup=edit_experience_inline_kbs(experience_choices))
    else:
        if handle_api_unauthorized_error(callback_query, experience_choices):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении опыта работы.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data.startswith('toggle_exp:'))
async def toggle_experience_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    new_exp_option, status = data[1], data[2]
    data = {
        'experience': new_exp_option
    }
    if status != "selected":
        auth_token = await get_applicant_auth_token(user_id)
        success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
        if success:
            success_markup, experiences = await get_all_available_experience_choices_with_applicant_option(auth_token, user_id)
            await callback_query.message.edit_reply_markup(reply_markup=edit_experience_inline_kbs(experiences))
            await callback_query.answer(f"Опыт работы изменен на {new_exp_option.lower()}")
        else:
            if handle_api_unauthorized_error(callback_query, _):
                return 
            await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении опыта работы.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data == 'edit-work_formats')
async def edit_applicant_work_formats(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    auth_token = await get_applicant_auth_token(user_id)
    success, work_formats = await get_all_available_work_formats_with_applicant_options(token_key=auth_token, user_id=user_id)
    if success:
        await callback_query.message.edit_text("Выберите предпочитаемые форматы работы: ", reply_markup=edit_work_formats_inline_kbs(work_formats))
    else:
        if handle_api_unauthorized_error(callback_query, work_formats):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении форматов работы.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data.startswith('toggle_wf:'))
async def toggle_work_formats_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    wf_option, wf_id, status = data[1], data[2], data[3]

    auth_token = await get_applicant_auth_token(user_id)
    success_found_list, list_of_applicant_work_formats_ids = await get_all_applicant_selected_work_formats_ids(token_key=auth_token, user_id=user_id)
    if success_found_list:
        if status == "selected":
            list_of_applicant_work_formats_ids.remove(wf_id)
            data = {
                'preferred_work_formats': list_of_applicant_work_formats_ids,
            }
            success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
            if success:
                success_markup, work_formats = await get_all_available_work_formats_with_applicant_options(auth_token, user_id)
                await callback_query.message.edit_reply_markup(reply_markup=edit_work_formats_inline_kbs(work_formats))
                await callback_query.answer(f"Удалён формат - {wf_option}")
        elif status == "not_selected":
            list_of_applicant_work_formats_ids.append(wf_id)
            data = {
                'preferred_work_formats': list_of_applicant_work_formats_ids,
            }
            success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
            if success:
                success_markup, work_formats = await get_all_available_work_formats_with_applicant_options(auth_token, user_id)
                await callback_query.message.edit_reply_markup(reply_markup=edit_work_formats_inline_kbs(work_formats))
                await callback_query.answer(f"Добавлен новый формат - {wf_option}")
    else:
        if handle_api_unauthorized_error(callback_query, list_of_applicant_work_formats_ids):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении форматов работы.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data == "edit-specializations")
async def edit_applicant_specializations(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    auth_token = await get_applicant_auth_token(user_id)
    success, specializations_list = await get_all_available_specializations_with_applicant_options(token_key=auth_token, user_id=user_id)
    if success:
        await callback_query.message.edit_text("Выберите виды специализаций: ", reply_markup=edit_specializations_inline_kbs(specializations_list))
    else:
        if handle_api_unauthorized_error(callback_query, specializations_list):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении специализаций.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data.startswith("toggle_spec:"))
async def toggle_specializations_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    spec_id, status = data[1], data[2]

    auth_token = await get_applicant_auth_token(user_id)
    spec_name = await toggle_specialization_name(spec_id=spec_id)
    success_found_list, list_of_applicant_specializations_ids = await get_all_applicant_selected_specializations_ids(token_key=auth_token, user_id=user_id)
    if success_found_list:
        if status == "selected":
            list_of_applicant_specializations_ids.remove(spec_id)
            data = {
                'specializations': list_of_applicant_specializations_ids
            }
            success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
            if success:
                success_markup, specializations = await get_all_available_specializations_with_applicant_options(auth_token, user_id)
                await callback_query.message.edit_reply_markup(reply_markup=edit_specializations_inline_kbs(specializations))
                await callback_query.answer(f"Убрана специализация - {spec_name}")
        elif status == "not_selected":
            list_of_applicant_specializations_ids.append(spec_id)
            data = {
                'specializations': list_of_applicant_specializations_ids
            }
            success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
            if success:
                success_markup, specializations = await get_all_available_specializations_with_applicant_options(auth_token, user_id)
                await callback_query.message.edit_reply_markup(reply_markup=edit_specializations_inline_kbs(specializations))
                await callback_query.answer(f"Добавлена специализация - {spec_name}")
    else:
        if handle_api_unauthorized_error(callback_query, list_of_applicant_specializations_ids):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении специализаций.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data.startswith('edit-notifications:'))
async def edit_applicant_notifications_switch(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    status = True if callback_query.data.split(":")[1] == 'True' else False
    data = {
        'notifications_enabled': not status
    }
    auth_token = await get_applicant_auth_token(user_id=user_id)
    success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
    if success:
        applicant_data_success, applicant_data = await get_applicant_info_by_telegram_id(callback_query.from_user.id)
        await callback_query.message.edit_reply_markup(reply_markup=edit_profile_inline_kbs(applicant_data))
        text = "Вы включили оповещения" if data["notifications_enabled"] else "Вы выключили оповещения" 
        await callback_query.answer(text)
    else:
        if handle_api_unauthorized_error(callback_query, _):
            return 
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении специализаций.", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data == 'edit-technologies-start-message')
async def edit_technologies_start_message(callback_query: CallbackQuery, state: FSMContext):
    await callback_query.message.edit_text('Введите название технологии (например, Python или Docker)')
    await state.set_state(TechnologyState.typing_tech)

@profile_router.message(TechnologyState.typing_tech)
async def process_finding_technologies_by_q(message: Message, state: FSMContext):
    user_id = message.from_user.id
    data = {
        'query': message.text
    }
    auth_token = await get_applicant_auth_token(user_id)
    success, found_technologies_by_query = await get_technologies_by_query(data=data, token_key=auth_token, user_id=user_id)
    if success:
        await state.update_data(current_tech_query=message.text)
        if len(found_technologies_by_query) > 0:
            await message.answer(f'По вашему запросу: <b><i>{message.text}</i></b> было найдено несколько вариантов технологий', parse_mode="html", reply_markup=edit_applicant_technologies_inline_kbs(found_technologies_by_query))
        else:
            await message.answer(f'По вашему запросу: <b><i>{message.text}</i></b> не нашлось ни одного варианта технологии ;(', parse_mode="html", reply_markup=go_back_to_editing_profile_or_stop_search_inline_kbs())
    else:
        if await handle_api_unauthorized_error(message, found_technologies_by_query):
            return 
        await message.answer("Упс! Что-то пошло не так при обновлении технологий!", reply_markup=go_back_to_editing_profile_inline_kbs())


@profile_router.callback_query(F.data.startswith('toggle_tech:'))
async def toggle_technologies_handler(callback_query: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    latest_query = user_data.get('current_tech_query')
    user_id = callback_query.from_user.id
    data = callback_query.data.split(":")
    tech_id, status = data[1], data[2]

    auth_token = await get_applicant_auth_token(user_id)
    tech_name = await toggle_technology_name(tech_id)
    success_found_list, list_of_applicant_technologies_ids = await get_all_applicant_selected_technologies_ids(token_key=auth_token, user_id=user_id)
    if success_found_list:
        if status == "selected":
            list_of_applicant_technologies_ids.remove(tech_id)
            data = {
                'technologies': list_of_applicant_technologies_ids
            }
            success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
            if success:
                success, found_technologies_by_query = await get_technologies_by_query(data={'query': latest_query}, token_key=auth_token, user_id=user_id)
                await callback_query.message.edit_reply_markup(reply_markup=edit_applicant_technologies_inline_kbs(found_technologies_by_query))
                await callback_query.answer(f"Убрана технология - {tech_name}")
        elif status == "not_selected":
            list_of_applicant_technologies_ids.append(tech_id)
            data = {
                'technologies': list_of_applicant_technologies_ids
            }
            success, _ = await edit_applicant_profile(data=data, token_key=auth_token, user_id=user_id)
            if success:
                success, found_technologies_by_query = await get_technologies_by_query(data={'query': latest_query}, token_key=auth_token, user_id=user_id)
                await callback_query.message.edit_reply_markup(reply_markup=edit_applicant_technologies_inline_kbs(found_technologies_by_query))
                await callback_query.answer(f"Добавлена технология - {tech_name}")
    else:
        if await handle_api_unauthorized_error(callback_query, list_of_applicant_technologies_ids):
            return
        await callback_query.message.edit_text("Упс! Что-то пошло не так при обновлении технологий!", reply_markup=go_back_to_editing_profile_inline_kbs())

@profile_router.callback_query(F.data == "stop_technologies_search")
async def stop_technologies_search_handler(callback_query: CallbackQuery, state: FSMContext):
    await state.clear() # очищаем состояния
    success, applicant_data = await get_applicant_info_by_telegram_id(callback_query.from_user.id)
    if success:
        await callback_query.message.edit_text("Выберите поле для редактирования:", reply_markup=edit_profile_inline_kbs(applicant_data))
    else:
        if await handle_api_unauthorized_error(callback_query, applicant_data):
            return
        await callback_query.message.edit_text('Произошла непредвиденная ошибка. Пожалуйста, повторите запрос позже')