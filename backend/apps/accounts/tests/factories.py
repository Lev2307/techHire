import hmac
import hashlib

from config import settings
from apps.vacancies.models import WorkFormat

def generate_hash_for_tests(data: dict):
    '''Генерация хэша для тестов'''
    secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
    check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
    new_hash = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
    return new_hash

def generate_applicant_additional_fields_for_sign_up(specs: list, techs: list, tg_user_data={}):
    return {
        'city': "Moscow",
        'specializations': [specs[0], specs[4]],
        'technologies': [techs[3], techs[5], techs[7]],
        'preferred_work_formats': [WorkFormat.objects.get(name_eng='ON_SITE').id],
        "tg_user_data": tg_user_data
    }