from datetime import datetime, timedelta
import concurrent.futures

import requests

from ..cache import get_user_city_info_from_cache_hh, get_hh_vacancy_from_cache
from ..models import Vacancy, WorkFormat, EDUCATION_CHOICES, EXPERIENCE_CHOICES, WORK_FORMAT_CHOICES, INITIAL_SOURCES
from ..helpers import extract_duties_requirements_working_conditions_by_keywords, get_payment_from_hh_vacancy
from .constants import NOT_FOUND_DUTIES, NOT_FOUND_REQS, NOT_FOUND_WORK_COND, HH_API_HEADERS, NUMBER_OF_VACANCIES_TO_BE_FOUND

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
    experience = [i for i in EXPERIENCE_CHOICES if i[1] == hh_vacancy_data["experience"]["name"]][0]
    employer = hh_vacancy_data["employer"]
    address = "Адрес компании не предоставлен" if hh_vacancy_data["address"] == None else hh_vacancy_data["address"]["raw"]
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
            'by_agreement': True if payment_from == 0 and payment_to == 0 else False
        },
        'work_formats': work_format_values,
        'experience': experience[0],
        'experience_ru': experience[1],
        'date_published': datetime.strptime(hh_vacancy_data["created_at"], "%Y-%m-%dT%H:%M:%S%z"),
        'is_added_to_favorites': Vacancy.objects.filter(external_id=hh_vacancy_data["id"]).exists(),
        'initial_source': INITIAL_SOURCES[1][0],
        'employer': {
            'name': employer["name"],
            'address': address,
            'alternate_url': employer['alternate_url'] if employer.get('alternate_url') else '',
        }
    }

def override_hh_vacancy_data_to_own_format(vacancies: list, headers: dict) -> list:
    '''
        Переопределение данных вакансий, полученных из API HH, в собственный унифицированный формат
    '''
    for i in range(len(vacancies)):
        vacancy_desc = get_hh_vacancy_from_cache(vacancies[i]["id"], headers, get_only_desc=True)
        if vacancy_desc != {}:
            parsed_options = extract_duties_requirements_working_conditions_by_keywords(vacancy_desc)
            
            vacancy_overrided = parse_vacancy_hh_data(vacancies[i], parsed_options)
            vacancies[i].clear()
            vacancies[i] = vacancy_overrided
        else:
            vacancies[i].clear()
    return vacancies


def hh_fetch_page(page, params, headers):
    params["page"] = page
    response = requests.get("https://api.hh.ru/vacancies", headers=headers, params=params).json()
    return response


def get_vacancies_from_headhunter_source(query: str, applicant_city_ru_format: str, salary_from: int, pages_count: int, are_for_recommendations: bool, count=NUMBER_OF_VACANCIES_TO_BE_FOUND) -> list:
    """Возвращает вакансии с api HH.ru, отфильтрованные по пользовательским критериям: ключевые слова - query, город - area, сфера IT - professional_role, минимальная зарплата (опционально) - salary"""
    city = get_user_city_info_from_cache_hh(applicant_city_ru_format, HH_API_HEADERS)
    params = {
        'per_page': count,
        'text': query,
        'area': city,
        'professional_role': ['156', '160', '10', '12', '150', '25', '165', '34', '36', '73', '155', '96', '164', '104', '157', '107', '112', '113', '148', '114', '116', '121', '124', '125', '126'],
        'order_by': 'relevance'
    }
    if not query:
        del params['text']

    if salary_from != 0:
        params["salary"] = salary_from
        params["only_with_salary"] = True

    if are_for_recommendations:
        params['order_by'] = 'publication_time'
    
    # if pages gt 1
    vacancies = []
    if pages_count > 1:
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(
                hh_fetch_page,
                page,
                params.copy(),
                HH_API_HEADERS
            ) for page in range(pages_count)]
            for future in concurrent.futures.as_completed(futures):
                page_data = future.result()
                vacancies.append(page_data.get("items", []))
        vacancies = [vacancy for sub_list in vacancies for vacancy in sub_list]
    else:
        response = requests.get("https://api.hh.ru/vacancies", headers=HH_API_HEADERS, params=params)
        vacancies = response.json().get("items")

    # оптимизация переопределения вакансий в нужный формат
    if are_for_recommendations:
        vacancies_partition = [[] for _ in range(pages_count)] # разбиение списка вакансий на отдельные списки по 100 штук каждый
        c, pos = 0, 0
        for i in range(len(vacancies)):
            c += 1
            vacancies_partition[pos].append(vacancies[i])
            if c == 100:
                pos += 1
                c = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            vacancies = []
            futures = [executor.submit(
                override_hh_vacancy_data_to_own_format,
                vacancies_partition[part].copy(),
                HH_API_HEADERS
            ) for part in range(len(vacancies_partition))]
            for future in concurrent.futures.as_completed(futures):
                for vac in future.result():
                    vacancies.append(vac)
            # print(f'all vacancies overrided - {len(vacancies)}')
    else:   
        vacancies = override_hh_vacancy_data_to_own_format(vacancies, headers=HH_API_HEADERS)
    return vacancies


def get_hh_vacancy_data_from_api(external_id: str) -> dict:
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