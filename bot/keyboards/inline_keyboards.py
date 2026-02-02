from aiogram.utils.keyboard import InlineKeyboardBuilder

def start_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="⚙️ Настройки", callback_data="profile")
    return builder.as_markup()

def profile_inline_kbs():
    builder = InlineKeyboardBuilder()
    builder.button(text="🏠 Вернуться в главную", callback_data="go_to_start")
    builder.button(text="✏️ Редактировать профиль", callback_data="edit_profile_start_message")
    return builder.as_markup()

def edit_profile_inline_kbs(applicant_data):
    notifications_enabled = "✅" if applicant_data.get('notifications_enabled') else "❌"
    
    builder = InlineKeyboardBuilder()
    builder.button(text=f"👤 Имя: {applicant_data.get('first_name')}", callback_data="edit-first_name")
    builder.button(text=f"🏙️ Город: {applicant_data.get('city')}", callback_data="edit-city")
    builder.button(text=f"💼 Опыт: {applicant_data.get('experience')}", callback_data="edit-experience")
    builder.button(text="🛠️ Формат работы", callback_data="edit-work_formats")
    builder.button(text="👨🏻‍💻 Специализации", callback_data="edit-specializations")
    builder.button(text="</> Технологии", callback_data="edit-technologies")
    builder.button(text=f"{notifications_enabled} Оповещения", callback_data="edit-notifications")
    builder.button(text="🏠 Вернуться в главную", callback_data="go_to_start")
    builder.adjust(1)
    return builder.as_markup()

def login_inline_keyboard():
    pass