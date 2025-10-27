from datetime import datetime
import re

import requests
from bs4 import BeautifulSoup

from config.settings import SUPERJOB_API_KEY
from ..accounts.models import Applicant, CITY_CHOICES, GENDER_CHOICES, EXPERIENCE_CHOICES
from .models import INITIAL_SOURCES, PLACE_OF_WORK_CHOICES

GENDERS_SUPERJOB = [
    ('0', GENDER_CHOICES[0][0]),
    ('2', GENDER_CHOICES[1][0]),
    ('3', GENDER_CHOICES[2][0])
]

TOWNS_SUPERJOB = [
    ('4', CITY_CHOICES[0][0]),
    ('14', CITY_CHOICES[1][0])
]

EDUCATIONS_SUPERJOB = [
    (0, 'not specified', 'Не имеет значения'),
    (2, 'Higher', 'Высшее'),
    (3, 'Incomplete_higher', 'Неполное высшее'),
    (4, 'Secondary_special', 'Средне-специальное'),
    (5, 'Secondary', 'Среднее'),
    (6, 'Student', 'Учащийся'),
]


#[{'id': 4, 'id_region': 46, 'id_country': 1, 'title': 'Москва', 'title_eng': 'Moscow'}, {'id': 14, 'id_region': 41, 'id_country': 1, 'title': 'Санкт-Петербург', 'title_eng': 'Saint-Petersburg'}, {'id': 13, 'id_region': 50, 'id_country': 1, 'title': 'Новосибирск', 'title_eng': 'Novosibirsk'}, {'id': 33, 'id_region': 65, 'id_country': 1, 'title': 'Екатеринбург', 'title_eng': 'Ekaterinburg'}, {'id': 12, 'id_region': 22, 'id_country': 1, 'title': 'Нижний Новгород', 'title_eng': 'Nizhnii Novgorod'}, {'id': 73, 'id_region': 60, 'id_country': 1, 'title': 'Ростов-на-Дону', 'title_eng': 'Rostov-na-Donu'}, {'id': 56, 'id_region': 8, 'id_country': 1, 'title': 'Хабаровск', 'title_eng': 'Khabarovsk'}, {'id': 55, 'id_region': 92, 'id_country': 1, 'title': 'Казань', 'title_eng': "Kazan'"}, {'id': 106, 'id_region': 75, 'id_country': 1, 'title': 'Челябинск', 'title_eng': 'Chelyabinsk'}, {'id': 17, 'id_region': 52, 'id_country': 1, 'title': 'Омск', 'title_eng': 'Omsk'}, {'id': 5, 'id_region': 36, 'id_country': 1, 'title': 'Самара', 'title_eng': 'Samara'}, {'id': 173, 'id_region': 80, 'id_country': 1, 'title': 'Уфа', 'title_eng': 'Ufa'}, {'id': 130, 'id_region': 4, 'id_country': 1, 'title': 'Красноярск', 'title_eng': 'Krasnoyarsk'}, {'id': 422, 'id_region': 105, 'id_country': 1, 'title': 'Донецк (Донецкая область)', 'title_eng': 'Donetsk'}, {'id': 119, 'id_region': 57, 'id_country': 1, 'title': 'Пермь', 'title_eng': "Perm'"}, {'id': 42, 'id_region': 20, 'id_country': 1, 'title': 'Воронеж', 'title_eng': 'Voronezh'}, {'id': 89, 'id_region': 18, 'id_country': 1, 'title': 'Волгоград', 'title_eng': 'Volgograd'}, {'id': 495, 'id_region': 108, 'id_country': 1, 'title': 'Запорожье', 'title_eng': "Zaporozh'e"}, {'id': 146, 'id_region': 63, 'id_country': 1, 'title': 'Саратов', 'title_eng': 'Saratov'}, {'id': 25, 'id_region': 3, 'id_country': 1, 'title': 'Краснодар', 'title_eng': 'Krasnodar'}]
def generate_user_info_for_superjob_api_request(city: str, gender: str) -> dict:
    '''Возврашает словарь с подходящими данными для запроса к api Superjob
        Например, city -> Москва переводится в id города, который видит api Superjob
    '''
    city_for_api, gender_for_api = '', ''
    for gen in GENDERS_SUPERJOB:
        if gender == gen[1]:
            gender_for_api = gen[0]
    for town in TOWNS_SUPERJOB:
        if city == town[1]:
            city_for_api = town[0]
    data = {
        't': city_for_api,
        'gender': gender_for_api,
    }
    return data

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
    
    
def get_vacancies_from_superjob_source(query, user, salary_from):
    url = f"https://api.superjob.ru/2.0/vacancies/"
    headers = {'X-Api-App-Id': SUPERJOB_API_KEY}
    user_info = generate_user_info_for_superjob_api_request(user.city, user.gender)
    params = {
        'count': 10,
        'order_field': 'relevance',
        'sort_new': 1,
        'keyword': query,
        'catalogues': '33',
        'payment_from': salary_from,
        't': user_info['t'],
        'gender': user_info['gender'],
    }
    if salary_from < 50_000:
        del params['payment_from']

    response = requests.get(url, headers=headers, params=params)
    vacancies = response.json().get("objects", [])
    removed_vacancies = []
    
    for vac in vacancies:
        text = vac['candidat']
        parsed_options = extract_duties_and_requirements_by_keywords(text)
        del vac['candidat']
        vac['duties'] = parsed_options['duties']
        vac['requirements'] = parsed_options['requirements']
        vac['vacancy_initial_source'] = INITIAL_SOURCES[0][0]
        if vac['duties'] == [] or vac['requirements'] == []:
            removed_vacancies.append(vac)

    return [i for i in vacancies if i not in removed_vacancies]
def get_vacancies_from_combined_api_sources(query: str, user: Applicant, salary_from: int) -> dict:
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from)
    # headhunter_vac = get_vacancies_from_headhunter_source(query, salary_from, user)
    headhunter_vacancies = []

    return superjob_vacancies + headhunter_vacancies

def get_vacancy_from_api(external_id: int, source: str):
    headers = {'X-Api-App-Id': SUPERJOB_API_KEY}
    if source == INITIAL_SOURCES[0][0]:
        superjob_url = f"https://api.superjob.ru/2.0/vacancies/{external_id}/"
        response = requests.get(superjob_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            print(data)
            parsed_text = extract_duties_and_requirements_by_keywords(data["candidat"])
            duties, reqs = "; ".join(parsed_text["duties"]), "; ".join(parsed_text["requirements"])
            valid_till = datetime.fromtimestamp(data["date_pub_to"])
            exp, ed, pl = data["experience"]["title"], data["education"]["id"], data["place_of_work"]["title"]
            for ch_exp in EXPERIENCE_CHOICES:
                if ch_exp[1] in exp:
                    exp = ch_exp[0]
                    break
            for ch_ed in EDUCATIONS_SUPERJOB:
                if ch_ed[0] == ed:
                    ed = ch_ed[1]
            for ch_pl in PLACE_OF_WORK_CHOICES:
                if ch_pl[1] in pl:
                    pl = ch_pl[0]
                    break
            return {
                "initial_source": source,
                "external_id": external_id,
                "duties": duties,
                "reqs": reqs,
                "title": data["profession"],
                "payment_from": data["payment_from"],
                "payment_to": data["payment_to"],
                "experience": exp,
                "education": ed,
                "place_of_work": pl,
                "valid_until": valid_till,
                "link": data["link"],
            }
        return {}