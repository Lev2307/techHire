import re
from bs4 import BeautifulSoup

from ..accounts.models import GENDER_CHOICES, CITY_CHOICES

GENDERS_SUPERJOB = [
    ('0', GENDER_CHOICES[0][0]),
    ('2', GENDER_CHOICES[1][0]),
    ('3', GENDER_CHOICES[2][0])
]

TOWNS_SUPERJOB = [
    ('4', CITY_CHOICES[0][0]),
    ('14', CITY_CHOICES[1][0])
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