from aiogram import Router, F
from aiogram.types import CallbackQuery

from api_handlers.handlers import get_applicant_auth_token, get_applicant_favourite_vacancies_list, get_favourite_vacancy_work_formats_names, remove_vacancy_from_favourites
from handlers.auth import handle_api_unauthorized_error
from keyboards.inline_keyboards import go_back_inline_kbs, favourite_vacancy_inline_kbs
from utils.factories import prepare_vacancy_text_for_message

favourites_router = Router()

@favourites_router.callback_query(F.data == "favourites_list")
async def favourites_list_handler(callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    auth_token = await get_applicant_auth_token(user_id)
    success_response, favourites_list = await get_applicant_favourite_vacancies_list(token_key=auth_token, user_id=user_id)
    if success_response:
        if len(favourites_list) > 0:
            await callback_query.message.edit_text('📋 Ваши избранные вакансии: ')
            for vacancy in favourites_list:
                success, vacancy_work_formats = await get_favourite_vacancy_work_formats_names(vac_id=vacancy.get('id'), token_key=auth_token, user_id=user_id)
                vacancy["work_formats"] = vacancy_work_formats
                vacancy_text = prepare_vacancy_text_for_message(vacancy_data=vacancy)

                await callback_query.message.answer(vacancy_text, parse_mode="html", reply_markup=favourite_vacancy_inline_kbs(respond_url=vacancy.get('original_link'), vac_id=vacancy.get('id')))
        else:
            await callback_query.message.edit_text('📭 <b>У вас отсутствуют избранные вакансии!</b> Ищите, смотрите и добавляйте понравившиеся вакансии в избранное в сервисе Techhire!', parse_mode="html", reply_markup=go_back_inline_kbs())
    else:
        if await handle_api_unauthorized_error(callback_query, favourites_list):
            return 
        await callback_query.message.edit_text('Произошла непредвиденная ошибка. Пожалуйста, повторите запрос позже')

@favourites_router.callback_query(F.data.startswith("remove_favourite_from_list:"))
async def remove_favourite_vacancy_handler(callback_query: CallbackQuery):
    vacancy_id = callback_query.data.split(":")[1]
    user_id = callback_query.from_user.id
    auth_token = await get_applicant_auth_token(user_id)
    success_destroy, response_data = await remove_vacancy_from_favourites(vac_id=vacancy_id, token_key=auth_token, user_id=user_id)
    if success_destroy:
        await callback_query.answer(response_data.get("message"))
        await callback_query.message.delete()
    else:
        if await handle_api_unauthorized_error(callback_query, response_data):
            return 
        await callback_query.message.edit_text('Произошла непредвиденная ошибка. Пожалуйста, повторите запрос позже')