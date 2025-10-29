from datetime import datetime

import requests

from config.settings import SUPERJOB_API_KEY
from ..accounts.models import Applicant, EXPERIENCE_CHOICES
from .models import Vacancy, INITIAL_SOURCES, PLACE_OF_WORK_CHOICES
from .helpers import generate_user_info_for_superjob_api_request, extract_duties_and_requirements_by_keywords

EDUCATIONS_SUPERJOB = [
    (0, 'not specified', 'Не имеет значения'),
    (2, 'Higher', 'Высшее'),
    (3, 'Incomplete_higher', 'Неполное высшее'),
    (4, 'Secondary_special', 'Средне-специальное'),
    (5, 'Secondary', 'Среднее'),
    (6, 'Student', 'Учащийся'),
]
    
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
        vac['is_added_to_favorites'] = Vacancy.objects.filter(external_id=vac["id"])
        

    return [i for i in vacancies if i not in removed_vacancies]
def get_vacancies_from_combined_api_sources(query: str, user: Applicant, salary_from: int) -> dict:
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from)
    # headhunter_vac = get_vacancies_from_headhunter_source(query, salary_from, user)
    headhunter_vacancies = []

    return superjob_vacancies + headhunter_vacancies

def get_vacancy_from_api(external_id: int, source: str):
    if source == INITIAL_SOURCES[0][0]:
        headers = {'X-Api-App-Id': SUPERJOB_API_KEY}
        superjob_url = f"https://api.superjob.ru/2.0/vacancies/{external_id}/"
        response = requests.get(superjob_url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            parsed_text = extract_duties_and_requirements_by_keywords(data["candidat"])
            duties, reqs = "; ".join(parsed_text["duties"]), "; ".join(parsed_text["requirements"])

            valid_till = datetime.fromtimestamp(data["date_pub_to"])
            exp, ed, pl = data["experience"]["title"], data["education"]["id"], data["place_of_work"]["title"]
            exp = [i[0] for i in EXPERIENCE_CHOICES if i[1] in exp][0]
            ed = [i[1] for i in EDUCATIONS_SUPERJOB if i[0] == ed][0]
            pl = [i[0] for i in PLACE_OF_WORK_CHOICES if i[1] in pl][0]

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