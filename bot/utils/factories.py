from datetime import datetime

import hmac
import hashlib

from babel.dates import format_datetime

def generate_telegram_oauth_hash(data: dict, bot_token: str):
    '''Генерация пользовательского хэша для логина в Techhire через телегу'''
    secret = hashlib.sha256(bot_token.encode()).digest()
    check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
    hash = hmac.new(secret, check_string.encode(), hashlib.sha256).hexdigest()
    return hash

def prepare_vacancy_text_for_message(vacancy_data: dict) -> str:
    '''Излечение данных из вакансии, объединение их в 1 текст для сообщения'''
    duties = "\n <b>•</b>".join(vacancy_data.get("duties").split(";")[:3])
    requirements = "\n <b>•</b>".join(vacancy_data.get("requirements").split(";")[:3])
    working_condititons = "\n <b>•</b>".join(vacancy_data.get("working_conditions").split(";")[:4])
    
    work_formats = ", ".join(vacancy_data.get("work_formats"))
    payment_text, payment_from, payment_to, curr = "", vacancy_data.get("payment_from"), vacancy_data.get("payment_to"), vacancy_data.get("currency")
    
    if payment_from == 0 and payment_to == 0:
        payment_text = '<i>Уровень дохода не указан</i>'
    elif payment_to == 0:
        payment_text = f'от <i>{payment_from}{curr}</i> за месяц'
    elif payment_from == 0:
        payment_text = f'до <i>{payment_to}{curr}</i> за месяц'
    elif payment_from == payment_to:
        payment_text = f'<i>{payment_to}{curr}</i> за месяц'
    else:
        payment_text = f'<i>{payment_from}-{payment_to}{curr}</i>'
    valid_until_dt = format_datetime(datetime.fromisoformat(vacancy_data.get("valid_until")), locale='ru', format='short')

    result = f"<b><i>{vacancy_data.get('title')}</i></b>" + f"\nЗарплата: {payment_text}" + f"\n\n🎯  <b>Задачи:</b>\n <b>•</b> {duties}"+ f"\n\n🛠  <b>Требования:</b>\n <b>•</b> {requirements}" + f"\n\n🤝  <b>Условия:</b>\n <b>•</b> {working_condititons}" + f"\n\nОпыт работы: <i>{vacancy_data.get('experience_ru')}</i>" + f"\nФормат(-ы): <i>{work_formats}</i>"
    result += f"\nСчитается действительной до: <b>{valid_until_dt}</b>"
    return result