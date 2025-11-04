import re
from datetime import datetime, timedelta

import requests

from config.settings import SUPERJOB_API_KEY, HH_API_ACCESS_TOKEN
from ..accounts.models import Applicant, EXPERIENCE_CHOICES
from .cache import get_user_city_info_from_cache_superjob, get_user_city_info_from_cache_hh, get_superjob_vacancy_from_cache, get_hh_vacancy_from_cache
from .models import Vacancy, INITIAL_SOURCES, PLACE_OF_WORK_CHOICES, EDUCATION_CHOICES
from .helpers import extract_duties_and_requirements_by_keywords

EDUCATIONS_SUPERJOB = [
    (0, 'not specified', 'Не имеет значения'),
    (2, 'Higher', 'Высшее'),
    (3, 'Incomplete_higher', 'Неполное высшее'),
    (4, 'Secondary_special', 'Средне-специальное'),
    (5, 'Secondary', 'Среднее'),
    (6, 'Student', 'Учащийся'),
]
EXPERIENCE_CHOICES_SUPERJOB = [
    (EXPERIENCE_CHOICES[0][0], 'Без опыта'),
    (EXPERIENCE_CHOICES[1][0], 'От 1 года'),
    (EXPERIENCE_CHOICES[2][0], 'От 3 лет'),
    (EXPERIENCE_CHOICES[3][0], 'От 6 лет'),
]
PLACE_OF_WORK_CHOICES_HH = [
    ("ON_SITE", PLACE_OF_WORK_CHOICES[0][0]),
    ("REMOTE", PLACE_OF_WORK_CHOICES[1][0]),
    ("HYBRID", PLACE_OF_WORK_CHOICES[2][0]),
]

HH_API_HEADERS = {
    "Authorization": f"Bearer {HH_API_ACCESS_TOKEN}",
    "User-Agent": "TechHire/1.0"
}
SUPERJOB_API_HEADERS = {
    'X-Api-App-Id': SUPERJOB_API_KEY
}

NOT_FOUND_DUTIES = "Отсутствует информация о задачах"
NOT_FOUND_REQS = "Отсутствует информация о требованиях"

def get_vacancies_from_superjob_source(query, user, salary_from):
    url = f"https://api.superjob.ru/2.0/vacancies/"
    city = get_user_city_info_from_cache_superjob(user.get_city_display(), SUPERJOB_API_HEADERS)
    params = {
        'count': 10,
        'order_field': 'relevance',
        'sort_new': 1,
        'keywords': query,
        'catalogues': '33',
        'payment_from': salary_from,
        't': city,
    }
    if salary_from < 50_000:
        del params['payment_from']

    response = requests.get(url, headers=SUPERJOB_API_HEADERS, params=params)
    vacancies = response.json().get("objects", [])
    removed_vacancies = []
    
    for vac in vacancies:
        text = vac['candidat']
        parsed_options = extract_duties_and_requirements_by_keywords(text)
        del vac['candidat']
        vac['duties'] = parsed_options['duties']
        vac['requirements'] = parsed_options['requirements']
        vac['vacancy_initial_source'] = INITIAL_SOURCES[0][0]
        vac['is_added_to_favorites'] = Vacancy.objects.filter(external_id=vac["id"])    
    return [i for i in vacancies if i not in removed_vacancies]
    

def get_vacancies_from_headhunter_source(query: str, user: Applicant, salary_from: int) -> dict:
    applicant_city_humanable = user.get_city_display()
    city = get_user_city_info_from_cache_hh(applicant_city_humanable, HH_API_HEADERS)
    params = {
        'per_page': 5,
        'text': query,
        'area': city,
        'professional_role': ['156', '160', '10', '12', '150', '25', '165', '34', '36', '73', '155', '96', '164', '104', '157', '107', '112', '113', '148', '114', '116', '121', '124', '125', '126'],
        'salary': salary_from,
        'order_by': 'relevance'
    }
    if salary_from < 50_000:
        del params["salary"]
    
    response = requests.get("https://api.hh.ru/vacancies", headers=HH_API_HEADERS, params=params)
    vacancies = response.json().get("items")
    for vac in vacancies:
        vac['vacancy_initial_source'] = INITIAL_SOURCES[1][0]
        vac['is_added_to_favorites'] = Vacancy.objects.filter(external_id=vac["id"])
        vacancy_desc = get_hh_vacancy_from_cache(vac["id"], HH_API_HEADERS, get_only_desc=True)
        parsed_options = extract_duties_and_requirements_by_keywords(vacancy_desc)
        vac["duties"] = parsed_options["duties"] if parsed_options["duties"] != [] else NOT_FOUND_DUTIES
        vac["requirements"] = parsed_options["requirements"] if parsed_options["requirements"] != [] else NOT_FOUND_REQS

    return vacancies

def get_vacancies_from_combined_api_sources(query: str, user: Applicant, salary_from: int) -> dict:
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from)
    headhunter_vacancies = get_vacancies_from_headhunter_source(query, user, salary_from)
    return headhunter_vacancies + superjob_vacancies

def get_vacancy_from_api(external_id: int, source: str):
    if source == INITIAL_SOURCES[0][0]:
        data = get_superjob_vacancy_from_cache(external_id, SUPERJOB_API_HEADERS)
        if data:
            parsed_text = extract_duties_and_requirements_by_keywords(data["candidat"])
            duties, reqs = "; ".join(parsed_text["duties"]), "; ".join(parsed_text["requirements"])

            valid_until = datetime.fromtimestamp(data["date_pub_to"])
            exp, ed, pl = data["experience"]["title"], data["education"]["id"], data["place_of_work"]["title"]
            exp = [i[0] for i in EXPERIENCE_CHOICES_SUPERJOB if exp == i[1]][0]
            ed = [i[1] for i in EDUCATIONS_SUPERJOB if i[0] == ed][0]
            pl = [i[0] for i in PLACE_OF_WORK_CHOICES if i[1] in pl][0]


            return {
                "initial_source": source,
                "external_id": external_id,
                "duties": duties if duties else NOT_FOUND_DUTIES,
                "reqs": reqs if reqs else NOT_FOUND_REQS,
                "title": data["profession"],
                "payment_from": data["payment_from"],
                "payment_to": data["payment_to"],
                "currency" : "RUR",
                "experience": exp,
                "education": ed,
                "place_of_work": pl,
                "valid_until": valid_until,
                "link": data["link"],
            }
        return 'Error'
    elif source == INITIAL_SOURCES[1][0]:
        data = get_hh_vacancy_from_cache(external_id, SUPERJOB_API_HEADERS)
        if data:
            parsed_text = extract_duties_and_requirements_by_keywords(data["description"])
            duties, reqs = "; ".join(parsed_text["duties"]), "; ".join(parsed_text["requirements"])
            valid_until = datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%S%z") + timedelta(days=30)
            exp = [i[0] for i in EXPERIENCE_CHOICES if i[1] in data["experience"]["name"]][0]

            if not data.get("education"):
                ed = EDUCATION_CHOICES[0][0]
            else:
                ed = [i[0] for i in EDUCATION_CHOICES if i[1] in data["education"]["name"]][0]

            if not data["work_format"]:
                pl = PLACE_OF_WORK_CHOICES[2][0]
            else:
                pl = [i[1] for i in PLACE_OF_WORK_CHOICES_HH if i[0] == data["work_format"][0]["id"]][0]

            if data["salary"] == None:
                payment_from, payment_to = 0, 0
            else:
                payment_from = 0 if data["salary"]["from"] == None else data["salary"]["from"]
                payment_to = 0 if data["salary"]["to"] == None else data["salary"]["to"]
            print(duties, reqs)
            return {
                "initial_source": source,
                "external_id": external_id,
                "duties": duties if duties else NOT_FOUND_DUTIES,
                "reqs": reqs if reqs else NOT_FOUND_REQS,
                "title": data["name"],
                "payment_from": payment_from,
                "payment_to": payment_to,
                "currency": "RUR" if data["salary"] == None else data["salary"]["currency"],
                "experience": exp,
                "education": ed,
                "place_of_work": pl,
                "valid_until": valid_until,
                "link": data["alternate_url"],
            }
        return 'Error'