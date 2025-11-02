import re

import requests
from bs4 import BeautifulSoup
from django.core.cache import cache

SECTION_DUTIES_NAMES = r'Чем предстоит заниматься[:\n]|Задачи[:\n]|Что нужно будет делать[:\n]|Что надо будет делать[:\n]|Основные задачи[:\n]|вы будете заниматься[:\n]|Обязанности[:\n]|Функциональные обязанности[:\n]|Что вы будете делать[:\n]|Ваши задачи[:\n]|Должностные обязанности[:\n]|Основные обязанности[:\n]|В ваши обязанности входит[:\n]|Вы будете заниматься[:\n]'
SECTION_REQUIREMENTS_NAMES = r'Наши ожидания[:\n]|у Вас есть[:\n]|Что мы ждем от Вас[:\n]|Вы точно нам подходите, если вы уверенный специалист хотя бы в одной из этих областей[:\n]|Наши пожелания[:\n]|Мы ожидаем уверенные знания[:\n]|Что для нас важно[:\n]|Что мы ожидаем от кандидата[:\n]|От вас нужно[:\n]|Мы ищем кандидата, который[:\n]|Обязательные требования[:\n]|Требования[:\n]|Желательно[:\n]|Требования и навыки[:\n]|Что мы ожидаем[:\n]|Требования к кандидату[:\n]|Квалификация[:\n]|Необходимые навыки[:\n]|Опыт и навыки[:\n]|Профессиональные требования[:\n]|Ключевые требования[:\n]|Требования к соискателю[:\n]'

def extract_and_reorder_text(text, sdn, srn):
    '''
        Функция, которая на вход получает исходный текст вакансии (HTML), достаёт из него задачи и требования из вакансии и выводит текст (HTML) в порядке:
        1. Задачи
        2. Требования
        3. Оставшийся текст
    '''
    duties_patterns = [r'(?:' + sdn + r')[:\-\n]*']
    requirements_patterns = [r'(?:' + srn +  r')[:\-\n]*']

    responsibility_match = None
    for pattern in duties_patterns:
        match = re.search(pattern + r"(.*?)(?=\n\s*\n|\n(?:" + "|".join(requirements_patterns) + ")[:\-\n]*|$)", text, re.IGNORECASE | re.DOTALL)
        if match:
            responsibility_match = match
            break

    requirement_match = None
    for pattern in requirements_patterns:
        match = re.search(pattern + r"(.*?)(?=\n\s*\n|\n(?:" + "|".join(duties_patterns) + ")[:\-\n]*|$)", text, re.IGNORECASE | re.DOTALL)
        if match:
            requirement_match = match
            break

    responsibilities = responsibility_match.group(0).strip() if responsibility_match else ""
    requirements = requirement_match.group(0).strip() if requirement_match else ""
    if responsibility_match:
        text = text[:responsibility_match.start()] + text[responsibility_match.end():]
    if requirement_match:
        text = text[:requirement_match.start()] + text[requirement_match.end():]

    new_text = "\n\n".join(filter(None, [responsibilities, requirements, text]))

    return new_text

def extract_duties_and_requirements_by_keywords(text):
    '''
        Получает задачи/обязанности и требования к кандидату из текста вакансии при помощи регулярных выражений
        Возвращает словарь {
            `duties`: [слова/предложения],
            `requirements`: [слова/предложения],
        }
    '''
    text = text.replace('<strong>', '').replace('</strong>', '')
    text = extract_and_reorder_text(text, SECTION_DUTIES_NAMES, SECTION_REQUIREMENTS_NAMES) # получает HTML, где сначала идут задачи, потом требования
    keywords_of_the_end_of_the_duties_or_reqs = r"Большим конкурентным преимуществом будет[:]|Будет плюсом[:]|Наши технологии[:]|Что надо будет делать[:]|Какие вещи и технологии мы используем в работе[:]|Мы ожидаем уверенные знания[:]|Условия работы[:]|Про команду и рабочие процессы|Почему стоит выбрать нас[:]|Условия[:]|Будет преимуществом[:]|Вы гарантированно получите[:]|Мы предлагаем[:]|Что мы предлагаем[:]|Что мы предлагаем[:]|Что мы ожидаем от кандидата[:]|" + SECTION_REQUIREMENTS_NAMES + r'$)'
    
    patterns = {
        'duties': [
            r'(?:' + SECTION_DUTIES_NAMES + r')' + r'[\s\S]*?(?=\n(?:' + keywords_of_the_end_of_the_duties_or_reqs + r")",
        ],
        'requirements': [
            r'(?:' + SECTION_REQUIREMENTS_NAMES + r')' + r'[\s\S]*?(?=\n(?:' + keywords_of_the_end_of_the_duties_or_reqs + r")",
        ],
    }
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text(separator='\n', strip=True)

    # Функция для извлечения списка пунктов
    def extract_items(section_text):
        if not section_text:
            return []
        section_text = re.sub(
            r'^(?:' + SECTION_DUTIES_NAMES + '|' + SECTION_REQUIREMENTS_NAMES + ')' + r'.*?\n?',
            '',
            section_text,
            flags=re.IGNORECASE
        )

        items = [item.strip() for item in re.split(r'[•*\n;]', section_text) if item.strip() and item != '\u200b']
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
            