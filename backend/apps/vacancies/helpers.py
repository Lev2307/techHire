import re

import requests
from bs4 import BeautifulSoup
from django.core.cache import cache


def extract_duties_and_requirements_by_keywords(text):
    '''
        Получает задачи/обязанности и требования к кандидату из текста вакансии при помощи регулярных выражений
        Возвращает словарь {
            `duties`: [слова/предложения],
            `requirements`: [слова/предложения],
        }
    '''
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)
    patterns = {
        'duties': [
            r'(?:Ваши задачи:|Задачи:|Обязанности:|Функциональные обязанности:|Что вы будете делать:|Ваши задачи:|Должностные обязанности:|Основные задачи:|Основные обязанности:|В ваши обязанности входит:|Вы будете заниматься:)[\s\S]*?(?=\n(?:Обязательные требования:|Требования:|Желательно:|Требования и навыки:|Что мы ожидаем:|Требования к кандидату:|Квалификация:|Необходимые навыки:|Опыт и навыки:|Профессиональные требования:|Ключевые требования:|Требования к соискателю:$))',
        ],
        'requirements': [
            r'(?:Обязательные требования|Требования:|Желательно:|Требования и навыки:|Что мы ожидаем:|Требования к кандидату:|Квалификация:|Необходимые навыки:|Опыт и навыки:|Профессиональные требования:|Ключевые требования:|Требования к соискателю:)[\s\S]*?(?=\Условия:|Вы гарантированно получите:|Мы предлагаем:)',
        ],
    }
    # Функция для извлечения списка пунктов
    def extract_items(section_text):
        if not section_text:
            return []
        section_text = re.sub(
            r'^(?:Задачи:|Обязательные требования:|Нашими требованиями являются:|Обязанности:|Требования:|Требования и навыки:|Что мы ожидаем:|Требования к кандидату:|Квалификация:|Необходимые навыки:|Опыт и навыки:|Профессиональные требования:|Ключевые требования:|Требования к соискателю:).*?\n?',
            '',
            section_text,
            flags=re.IGNORECASE
        )

        items = [item.strip() for item in re.split(r'[•\n;]', section_text) if item.strip()]
        return items

    result = {}
    for key, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                result[key] = extract_items(match.group(0))
                break
        else:
            result[key] = [] 
    return result


def get_user_city_info_for_superjob_api_request(city: str, headers: dict) -> dict:
    if not cache.get(f"SUPERJOB_CITY_INFO_{city}"):
        url = f"https://api.superjob.ru/2.0/towns"
        response = requests.get(url, headers=headers)
        cities = response.json().get("objects", [])
        for j in cities:
            if j["title"] == city:
                cache.set(f"SUPERJOB_CITY_INFO_{city}", j)
                return j["id"]
    else:
        return cache.get(f"SUPERJOB_CITY_INFO_{city}")["id"]

def get_user_city_info_for_hh_api_request(city: str, headers: dict):
    if not cache.get(f"HH_CITY_INFO_{city}"):
        url = f"https://api.hh.ru/areas"
        response = requests.get(url, headers=headers)
        russian_cities = []
        for j in response.json():
            if j['name'] == 'Россия':
                russian_cities.append(j["areas"])
                break
        for c in russian_cities:
            for i in c:
                if i["name"] == city:
                    cache.set(f"HH_CITY_INFO_{city}", i)
                    return i["id"]
    else:
        return cache.get(f"HH_CITY_INFO_{city}")["id"]
            