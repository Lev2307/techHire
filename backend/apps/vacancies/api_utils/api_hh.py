from datetime import datetime, timedelta

import requests

from apps.accounts.models import Applicant
from ..cache import get_user_city_info_from_cache_hh, get_hh_vacancy_from_cache
from ..models import Vacancy, WorkFormat, EDUCATION_CHOICES, EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES, INITIAL_SOURCES
from ..helpers import extract_duties_requirements_working_conditions_by_keywords, get_payment_from_hh_vacancy
from .constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS, NOT_FOUND_WORK_COND, HH_API_HEADERS

def parse_vacancy_hh_data(hh_vacancy_data: dict, parsed_options: dict) -> dict:
    """Преобразовывает данные вакансии из api HH.ru в унифицированный формат."""
    payment_from, payment_to = get_payment_from_hh_vacancy(hh_vacancy_data["salary"])
    work_format_values = []
    if hh_vacancy_data["work_format"]:
        for wf in hh_vacancy_data["work_format"]:
            for wf_choice in WORK_FORMAT_CHOICES:
                if wf_choice[0] == wf["id"]:
                    work_format_values.append(WorkFormat.objects.get(name_eng=wf_choice[0]))
    else:
        work_format_values = [WorkFormat.objects.get(name_eng=WORK_FORMAT_CHOICES[0][0])]

    employer = hh_vacancy_data["employer"]
    address = "Адрес компании не предоставлен" if not hh_vacancy_data["address"] else hh_vacancy_data["address"]["raw"]

    return {
        'external_id': hh_vacancy_data["id"],
        'title': hh_vacancy_data["name"],
        'duties': parsed_options["duties"] if parsed_options["duties"] != [] else NOT_FOUND_DUTIES,
        'requirements': parsed_options["requirements"] if parsed_options["requirements"] != [] else NOT_FOUND_REQS,
        'working_conditions': parsed_options["working_conditions"] if parsed_options["working_conditions"] != [] else NOT_FOUND_WORK_COND,
        'payment': {
            'payment_from': payment_from,
            'payment_to': payment_to,
            'currency': "RUR" if hh_vacancy_data["salary"] == None else hh_vacancy_data["salary"]["currency"],
        },
        'work_formats': work_format_values,
        'experience': [i[0] for i in EXPERIENCE_CHOICES if i[1] == hh_vacancy_data["experience"]["name"]][0],
        'date_published': datetime.strptime(hh_vacancy_data["created_at"], "%Y-%m-%dT%H:%M:%S%z"),
        'is_added_to_favorites': Vacancy.objects.filter(external_id=hh_vacancy_data["id"]).exists(),
        'initial_source': INITIAL_SOURCES[1][0],
        'employer': {
            'name': employer["name"],
            'address': address,
            'alternate_url': employer["alternate_url"],
        }
    }

def get_vacancies_from_headhunter_source(query: str, user: Applicant, salary_from: int, count=30) -> dict:
    """Возвращает вакансии с api HH.ru, отфильтрованные по пользовательским критериям: ключевые слова - query, город - area, сфера IT - professional_role, минимальная зарплата (опционально) - salary"""
    applicant_city_humanable = user.get_city_display()
    city = get_user_city_info_from_cache_hh(applicant_city_humanable, HH_API_HEADERS)
    params = {
        'per_page': count,
        'text': query,
        'area': city,
        'professional_role': ['156', '160', '10', '12', '150', '25', '165', '34', '36', '73', '155', '96', '164', '104', '157', '107', '112', '113', '148', '114', '116', '121', '124', '125', '126'],
        'order_by': 'relevance'
    }
    if not query:
        del params['text']

    if salary_from:
        params["salary"] = salary_from
        params["only_with_salary"] = True
    
    response = requests.get("https://api.hh.ru/vacancies", headers=HH_API_HEADERS, params=params)
    vacancies = response.json().get("items")
    for i in range(len(vacancies)):
        vacancy_desc = get_hh_vacancy_from_cache(vacancies[i]["id"], HH_API_HEADERS, get_only_desc=True)
        parsed_options = extract_duties_requirements_working_conditions_by_keywords(vacancy_desc)
        
        vacancy_overrided = parse_vacancy_hh_data(vacancies[i], parsed_options)
        vacancies[i].clear()
        vacancies[i] = vacancy_overrided
    return vacancies


def get_hh_vacancy_data_from_api(external_id: str):
    """Возвращает данные о конкретной вакансии из api HH.ru и передаёт их во вью"""
    data = get_hh_vacancy_from_cache(external_id, HH_API_HEADERS)
    if data:
        parsed_text = extract_duties_requirements_working_conditions_by_keywords(data["description"])
        if not data.get("education"):
            ed = EDUCATION_CHOICES[0][0]
        else:
            ed = [i[0] for i in EDUCATION_CHOICES if i[1] in data["education"]["name"]][0]

        returned_data = parse_vacancy_hh_data(data, parsed_text)
        # Делаю каждый раздел из одной большой строки в список критериев, разделенных ;
        returned_data["duties"] = "; ".join(returned_data["duties"])
        returned_data["requirements"] = "; ".join(returned_data["requirements"])
        returned_data["working_conditions"] = "; ".join(returned_data["working_conditions"])

        # Добавляю доп данные о вакансии в бд, которых нет в parse_vacancy_hh_data
        returned_data["education"] = ed
        returned_data["valid_until"] = returned_data["date_published"] + timedelta(days=30)
        returned_data["original_link"] = data["alternate_url"]
        return returned_data
    return {}