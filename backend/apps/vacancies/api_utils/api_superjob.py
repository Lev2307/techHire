from datetime import datetime, timedelta
import concurrent

import requests

from ..cache import get_user_city_info_from_cache_superjob, get_superjob_vacancy_from_cache
from ..helpers import extract_duties_requirements_working_conditions_by_keywords
from ..models import Vacancy, WorkFormat, EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES, INITIAL_SOURCES
from .constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS, NOT_FOUND_WORK_COND, SUPERJOB_API_HEADERS, NUMBER_OF_VACANCIES_TO_BE_FOUND

EDUCATIONS_SUPERJOB = [
    (0, 'not specified', 'Не имеет значения'),
    (2, 'Higher', 'Высшее'),
    (3, 'Incomplete_higher', 'Неполное высшее'),
    (4, 'Secondary_special', 'Средне-специальное'),
    (5, 'Secondary', 'Среднее'),
    (6, 'Student', 'Учащийся'),
]
EXPERIENCE_CHOICES_SUPERJOB = [
    (EXPERIENCE_CHOICES[0][0], 'Без опыта', EXPERIENCE_CHOICES[0][1]),
    (EXPERIENCE_CHOICES[1][0], 'От 1 года', EXPERIENCE_CHOICES[1][1]),
    (EXPERIENCE_CHOICES[2][0], 'От 3 лет', EXPERIENCE_CHOICES[2][1]),
    (EXPERIENCE_CHOICES[3][0], 'От 6 лет', EXPERIENCE_CHOICES[3][1]),
]

def parse_vacancy_superjob_data(superjob_vacancy_data: dict, parsed_options: dict) -> dict:
    """Преобразовывает данные вакансии из api Superjob в унифицированный формат."""

    work_format_values = []
    for _ in range(len(WORK_FORMAT_CHOICES)):
        if _ == superjob_vacancy_data["place_of_work"]["id"]:
            work_format_values.append(WorkFormat.objects.get(name_eng=WORK_FORMAT_CHOICES[_][0]))

    employer = superjob_vacancy_data["client"]
    experience =  [_ for _ in EXPERIENCE_CHOICES_SUPERJOB if superjob_vacancy_data["experience"]["title"] == _[1]][0]
    return {
        'external_id': str(superjob_vacancy_data["id"]),
        'title': superjob_vacancy_data["profession"],
        'duties': parsed_options["duties"] if parsed_options["duties"] != [] else NOT_FOUND_DUTIES,
        'requirements': parsed_options["requirements"] if parsed_options["requirements"] != [] else NOT_FOUND_REQS,
        'working_conditions': parsed_options["working_conditions"] if parsed_options["working_conditions"] != [] else NOT_FOUND_WORK_COND,
        'payment': {
            'payment_from': superjob_vacancy_data["payment_from"],
            'payment_to': superjob_vacancy_data["payment_to"],
            'currency': "RUR",
            'by_agreement': True if superjob_vacancy_data["payment_from"] == 0 and superjob_vacancy_data["payment_to"] == 0 else False
        },
        'work_formats': work_format_values,
        'experience': experience[0],
        'experience_ru': experience[2],
        'date_published': datetime.fromtimestamp(superjob_vacancy_data["date_published"]),
        'is_added_to_favorites': Vacancy.objects.filter(external_id=superjob_vacancy_data["id"]).exists(),
        'initial_source': INITIAL_SOURCES[0][0],
        'employer': {
            'name': employer["title"] if employer.get("title") else "",
            'address': "Адрес компании не предоставлен" if superjob_vacancy_data["address"] == None else superjob_vacancy_data["address"],
            'url': employer["link"] if employer.get("link") else "",
        }
    }

def superjob_fetch_page(page, params, headers):
    params["page"] = page
    response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=headers, params=params).json()
    return response

def get_vacancies_from_superjob_source(query: str, applicant_city_ru_format: str, salary_from: int, pages_count: int, are_for_recommendations: bool, count=NUMBER_OF_VACANCIES_TO_BE_FOUND) -> list:
    """Возвращает вакансии с api Superjob, отфильтрованные по пользовательским критериям: ключевые слова - keywords, город - t, сфера IT - catalogues, минимальная зарплата (опционально) - payment_from"""
    city = get_user_city_info_from_cache_superjob(applicant_city_ru_format, SUPERJOB_API_HEADERS)
    params = {
        'count': count,
        'order_field': 'relevance',
        'sort_new': 1,
        'keywords': query,
        'catalogues': '33',
        't': city,
    }
    if not query:
        del params["keywords"]

    if salary_from != 0 or are_for_recommendations:
        params['payment_from'] = salary_from

    vacancies = []
    if pages_count > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(
                superjob_fetch_page,
                page,
                params.copy(),
                SUPERJOB_API_HEADERS
            ) for page in range(pages_count)]
            for future in concurrent.futures.as_completed(futures):
                page_data = future.result()
                vacancies.append(page_data.get("objects", []))
        vacancies = [vacancy for sub_list in vacancies for vacancy in sub_list]
    else:
        response = requests.get("https://api.superjob.ru/2.0/vacancies/", headers=SUPERJOB_API_HEADERS, params=params)
        vacancies = response.json().get("objects")
    for i in range(len(vacancies)):
        text = vacancies[i]['candidat']
        parsed_options = extract_duties_requirements_working_conditions_by_keywords(text)
        vacancy_overrided = parse_vacancy_superjob_data(vacancies[i], parsed_options)
        vacancies[i].clear()
        vacancies[i] = vacancy_overrided
    # print(f'superjob vacancies - {len(vacancies)}')
    return vacancies

def get_superjob_vacancy_data_from_api(external_id: str) -> dict:
    """Возвращает данные о конкретной вакансии из api Superjob и передаёт их во вью"""
    data = get_superjob_vacancy_from_cache(external_id, SUPERJOB_API_HEADERS)
    if data:
        parsed_text = extract_duties_requirements_working_conditions_by_keywords(data["candidat"])
        valid_until = datetime.fromtimestamp(data["date_pub_to"]) + timedelta(days=1)
        ed = [i[1] for i in EDUCATIONS_SUPERJOB if i[0] == data["education"]["id"]][0]

        returned_data = parse_vacancy_superjob_data(data, parsed_text)
        # Делаю каждый раздел из одной большой строки в список критериев, разделенных ;
        returned_data["duties"] = "; ".join(returned_data["duties"])
        returned_data["requirements"] = "; ".join(returned_data["requirements"])
        returned_data["working_conditions"] = "; ".join(returned_data["working_conditions"])

        # Добавляю доп данные о вакансии в бд, которых нет в parse_vacancy_hh_data
        returned_data["education"] = ed
        returned_data["valid_until"] = valid_until
        returned_data["original_link"] = data["link"]
        return returned_data
    return {}