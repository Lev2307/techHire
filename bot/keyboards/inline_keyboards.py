from aiogram.utils.keyboard import InlineKeyboardBuilder

def start_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="⚙️ Настройки", callback_data="profile")
    builder.button(text="⭐ Избранные вакансии", callback_data="favourites_list")
    return builder.as_markup()

def profile_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Вернуться в главную", callback_data="go_to_start")
    builder.button(text="✏️ Редактировать профиль", callback_data="edit_profile_start_message")
    builder.button(text="🚫 Выйти из аккаунта", callback_data="logout")
    return builder.as_markup()

def edit_profile_inline_kbs(applicant_data):
    notifications_enabled = "✅" if applicant_data.get('notifications_enabled') else "❌"
    
    builder = InlineKeyboardBuilder()
    builder.button(text=f"👤 Имя: {applicant_data.get('first_name')}", callback_data="edit-first_name")
    builder.button(text=f"🏙️ Город: {applicant_data.get('city')}", callback_data="edit-city")
    builder.button(text=f"💼 Опыт: {applicant_data.get('experience')}", callback_data="edit-experience")
    builder.button(text="🛠️ Формат работы", callback_data="edit-work_formats")
    builder.button(text="👨🏻‍💻 Специализации", callback_data="edit-specializations")
    builder.button(text="</> Технологии", callback_data="edit-technologies-start-message")
    builder.button(text=f"{notifications_enabled} Оповещения", callback_data=f"edit-notifications:{applicant_data.get('notifications_enabled')}")
    builder.button(text="🏠 Вернуться в главную", callback_data="go_to_start")
    builder.adjust(1)
    return builder.as_markup()

def go_back_to_editing_profile_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Вернуться в главную", callback_data="go_to_start")
    builder.button(text="🔙 Назад", callback_data="edit_profile_start_message")
    return builder.as_markup()

def edit_city_inline_kbs(cities_data: dict):
    builder = InlineKeyboardBuilder()
    for key, value in cities_data.items(): # value ('город ру', 'selected/not_selected')
        mark = "✅" if value[1] == "selected" else ""
        builder.button(
            text=f"{mark} {value[0]}",
            callback_data=f"toggle_city:{key}:{value[1]}"
        )
    builder.button(text='✏️ Продолжить редактирование', callback_data="edit_profile_start_message")
    builder.adjust(2)
    return builder.as_markup()

def edit_experience_inline_kbs(experience_data: dict):
    builder = InlineKeyboardBuilder()
    for key, value in experience_data.items():
        mark = "✅" if value[1] == "selected" else ""
        builder.button(
            text=f"{mark} {value[0]}",
            callback_data=f"toggle_exp:{key}:{value[1]}"
        )
    builder.button(text='✏️ Продолжить редактирование', callback_data="edit_profile_start_message")
    builder.adjust(2, 2)
    return builder.as_markup()

def edit_work_formats_inline_kbs(work_formats: dict):
    builder = InlineKeyboardBuilder()
    for key, value in work_formats.items(): # {"ON_SITE": (id, 'очно', 'selected/not_selected')}
        mark = "✅" if value[2] == "selected" else ""
        builder.button(
            text=f"{mark} {value[1]}",
            callback_data=f"toggle_wf:{key}:{value[0]}:{value[2]}"
        )
    builder.button(text='✏️ Продолжить редактирование', callback_data="edit_profile_start_message")
    builder.adjust(3, 1)
    return builder.as_markup()

def edit_specializations_inline_kbs(specializations: list):
    builder = InlineKeyboardBuilder()
    for spec in specializations:
        mark = "✅" if spec['status'] == "selected" else ""
        builder.button(
            text=f"{mark} {spec['name']}",
            callback_data=f"toggle_spec:{spec['id']}:{spec['status']}"
        )
    builder.button(text='✏️ Продолжить редактирование', callback_data="edit_profile_start_message")
    builder.adjust(3, 3)
    return builder.as_markup()

def edit_applicant_technologies_inline_kbs(technologies: list):
    builder = InlineKeyboardBuilder()
    for tech in technologies:
        mark = "✅" if tech['status'] == "selected" else ""
        builder.button(
            text=f"{mark} {tech['name']}",
            callback_data=f"toggle_tech:{tech['id']}:{tech['status']}"
        )
    builder.button(text='🔍 Завершить поиск технологий', callback_data="stop_technologies_search")
    builder.adjust(2)
    return builder.as_markup()

def go_back_to_editing_profile_or_stop_search_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Вернуться в главную", callback_data="go_to_start")
    builder.button(text='🔍 Завершить поиск технологий', callback_data="stop_technologies_search")
    return builder.as_markup()

def login_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text='🔓 Повторная авторизация', callback_data="re-authorization")
    return builder.as_markup()

def go_back_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад", callback_data="go_to_start")
    return builder.as_markup()

def favourite_vacancy_inline_kbs(respond_url: str, vac_id: str):
    builder = InlineKeyboardBuilder()
    builder.button(
        text="🗑️ Удалить вакансию из избранного",
        callback_data=f"remove_favourite_from_list:{vac_id}"
    )
    builder.button(
        text="🌐 Полное описание вакансии на сайте",
        url="http://127.0.0.1:8000/vacancies/favorites/" # при создании фронта буду перекидывать туда. Пока что перекидывает на бэк
    )
    builder.button(
        text="💬 Откликнуться на вакансию",
        url=respond_url
    )
    builder.adjust(1)
    return builder.as_markup()