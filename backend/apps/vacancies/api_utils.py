from datetime import datetime, timedelta, timezone

import requests

from config.settings import SUPERJOB_API_KEY, HH_API_ACCESS_TOKEN
from ..accounts.models import Applicant, EXPERIENCE_CHOICES
from .cache import get_user_city_info_from_cache_superjob, get_user_city_info_from_cache_hh, get_superjob_vacancy_from_cache, get_hh_vacancy_from_cache
from .models import Vacancy, WorkFormat, INITIAL_SOURCES, WORK_FORMAT_CHOICES, EDUCATION_CHOICES
from .helpers import extract_duties_and_requirements_by_keywords, generate_appropriate_vacancy_data_for_search_response, get_payment_from_hh_vacancy

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


HH_API_HEADERS = {
    "Authorization": f"Bearer {HH_API_ACCESS_TOKEN}",
    "User-Agent": "TechHire/1.0"
}
SUPERJOB_API_HEADERS = {
    'X-Api-App-Id': SUPERJOB_API_KEY
}

NOT_FOUND_DUTIES = "Отсутствует информация о задачах"
NOT_FOUND_REQS = "Отсутствует информация о требованиях"
NOT_FOUND_WORK_COND = "Отсутствует информация об условиях работы"


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

    for i in range(len(vacancies)):
        text = vacancies[i]['candidat']
        parsed_options = extract_duties_and_requirements_by_keywords(text)

        work_format_values = []
        for i in range(len(WORK_FORMAT_CHOICES)):
            if i == vacancies[i]["place_of_work"]["id"]:
                work_format_values.append(WorkFormat.objects.get(name_eng=WORK_FORMAT_CHOICES[i][0]))

        pk, title = vacancies[i]["id"], vacancies[i]["profession"]
        payment_from, payment_to = vacancies[i]["payment_from"], vacancies[i]["payment_to"]
        employer = vacancies[i]["client"]
        date_published = datetime.fromtimestamp(vacancies[i]["date_published"])

        vacancies[i].clear()
        vacancy_overrided = generate_appropriate_vacancy_data_for_search_response(
            pk=pk,
            title=title,
            duties=parsed_options['duties'] if parsed_options["duties"] != [] else NOT_FOUND_DUTIES,
            reqs=parsed_options['requirements'] if parsed_options["requirements"] != [] else NOT_FOUND_REQS,
            work_cond=parsed_options["working_conditions"] if parsed_options["working_conditions"] != [] else NOT_FOUND_WORK_COND,
            payment_from=int(payment_from),
            payment_to=int(payment_to),
            currency="RUR",
            date_published=date_published.replace(tzinfo=timezone(timedelta(hours=3))),
            work_formats=work_format_values,
            initial_source=INITIAL_SOURCES[0][0],
            is_added_to_favorites=Vacancy.objects.filter(external_id=pk),   
            employer_name=employer["title"],
            employer_url=employer["link"]
        )
        vacancies[i] = vacancy_overrided

    return vacancies
    

def get_vacancies_from_headhunter_source(query: str, user: Applicant, salary_from: int) -> dict:
    applicant_city_humanable = user.get_city_display()
    city = get_user_city_info_from_cache_hh(applicant_city_humanable, HH_API_HEADERS)
    params = {
        'per_page': 23,
        'text': query,
        'area': city,
        'professional_role': ['156', '160', '10', '12', '150', '25', '165', '34', '36', '73', '155', '96', '164', '104', '157', '107', '112', '113', '148', '114', '116', '121', '124', '125', '126'],
        'order_by': 'relevance'
    }
    if salary_from:
        params["salary"] = salary_from
        params["only_with_salary"] = True
    
    response = requests.get("https://api.hh.ru/vacancies", headers=HH_API_HEADERS, params=params)
    vacancies = response.json().get("items")
    for i in range(len(vacancies)):

        vacancy_desc = get_hh_vacancy_from_cache(vacancies[i]["id"], HH_API_HEADERS, get_only_desc=True)
        parsed_options = extract_duties_and_requirements_by_keywords(vacancy_desc)
        payment_from, payment_to = get_payment_from_hh_vacancy(vacancies[i]["salary"])
        curr = "RUR" if vacancies[i]["salary"] == None else vacancies[i]["salary"]["currency"]
        pk, title, created_at = vacancies[i]["id"], vacancies[i]["name"], vacancies[i]["created_at"]
        employer = vacancies[i]["employer"]

        work_format_values = []
        if vacancies[i]["work_format"]:
            for wf in vacancies[i]["work_format"]:
                for wf_choice in WORK_FORMAT_CHOICES:
                    if wf_choice[0] == wf["id"]:
                        work_format_values.append(WorkFormat.objects.get(name_eng=wf_choice[0]))
        else:
            work_format_values = [WorkFormat.objects.get(name_eng=WORK_FORMAT_CHOICES[0][0])]

        vacancies[i].clear()
        vacancy_overrided = generate_appropriate_vacancy_data_for_search_response(
            pk=pk,
            title=title,
            reqs=parsed_options["requirements"] if parsed_options["requirements"] != [] else NOT_FOUND_REQS,
            duties=parsed_options["duties"] if parsed_options["duties"] != [] else NOT_FOUND_DUTIES,
            work_cond=parsed_options["working_conditions"] if parsed_options["working_conditions"] != [] else NOT_FOUND_WORK_COND,
            payment_from=payment_from,
            payment_to=payment_to,
            currency=curr,
            date_published=datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S%z"),
            work_formats=work_format_values,
            is_added_to_favorites=Vacancy.objects.filter(external_id=pk).exists(),
            initial_source=INITIAL_SOURCES[1][0],
            employer_name=employer["name"],
            employer_url=employer["alternate_url"],
        )
        vacancies[i] = vacancy_overrided
    return vacancies

def get_vacancies_from_combined_api_sources(query: str, user: Applicant, salary_from: int) -> dict:
    headhunter_vacancies = get_vacancies_from_headhunter_source(query, user, salary_from)
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from)

    return headhunter_vacancies + superjob_vacancies

def get_vacancy_from_api(external_id: int, source: str):
    if source == INITIAL_SOURCES[0][0]:
        data = get_superjob_vacancy_from_cache(external_id, SUPERJOB_API_HEADERS)
        if data:
            parsed_text = extract_duties_and_requirements_by_keywords(data["candidat"])
            duties, reqs, working_conditions = "; ".join(parsed_text["duties"]), "; ".join(parsed_text["requirements"]), "; ".join(parsed_text["working_conditions"])

            valid_until = datetime.fromtimestamp(data["date_pub_to"])
            exp, ed, wf = data["experience"]["title"], data["education"]["id"], data["place_of_work"]
            exp = [i[0] for i in EXPERIENCE_CHOICES_SUPERJOB if exp == i[1]][0]
            ed = [i[1] for i in EDUCATIONS_SUPERJOB if i[0] == ed][0]

            work_format_values = []
            for i in range(len(WORK_FORMAT_CHOICES)):
                if i == wf["id"]:
                    work_format_values.append(WorkFormat.objects.get(name_eng=WORK_FORMAT_CHOICES[i][0]))

            return {
                "initial_source": source,
                "external_id": external_id,
                "duties": duties if duties else NOT_FOUND_DUTIES,
                "reqs": reqs if reqs else NOT_FOUND_REQS,
                "working_conditions": working_conditions if working_conditions else NOT_FOUND_WORK_COND,
                "title": data["profession"],
                "payment_from": data["payment_from"],
                "payment_to": data["payment_to"],
                "currency" : "RUR",
                "experience": exp,
                "education": ed,
                "work_format": work_format_values,
                "valid_until": valid_until,
                "link": data["link"],
            }
        return 'Error'
    elif source == INITIAL_SOURCES[1][0]:
        data = get_hh_vacancy_from_cache(external_id, SUPERJOB_API_HEADERS)
        if data:
            parsed_text = extract_duties_and_requirements_by_keywords(data["description"])
            duties, reqs, working_cond = "; ".join(parsed_text["duties"]), "; ".join(parsed_text["requirements"]), "; ".join(parsed_text["working_conditions"])
            valid_until = datetime.strptime(data["published_at"], "%Y-%m-%dT%H:%M:%S%z")
            exp = [i[0] for i in EXPERIENCE_CHOICES if i[1] in data["experience"]["name"]][0]

            if not data.get("education"):
                ed = EDUCATION_CHOICES[0][0]
            else:
                ed = [i[0] for i in EDUCATION_CHOICES if i[1] in data["education"]["name"]][0]

            work_format_values = []
            if data["work_format"]:
                for wf in data["work_format"]:
                    for wf_choice in WORK_FORMAT_CHOICES:
                        if wf_choice[0] == wf["id"]:
                            work_format_values.append(WorkFormat.objects.get(name_eng=wf_choice[0]))
            else:
                work_format_values = [WorkFormat.objects.get(name_eng=WORK_FORMAT_CHOICES[0][0])]

            if data["salary"] == None:
                payment_from, payment_to = 0, 0
            else:
                payment_from = 0 if data["salary"]["from"] == None else data["salary"]["from"]
                payment_to = 0 if data["salary"]["to"] == None else data["salary"]["to"]

            return {
                "initial_source": source,
                "external_id": external_id,
                "duties": duties if duties else NOT_FOUND_DUTIES,
                "reqs": reqs if reqs else NOT_FOUND_REQS,
                "working_conditions": working_cond if working_cond else NOT_FOUND_WORK_COND,
                "title": data["name"],
                "payment_from": payment_from,
                "payment_to": payment_to,
                "currency": "RUR" if data["salary"] == None else data["salary"]["currency"],
                "experience": exp,
                "education": ed,
                "work_format": work_format_values,
                "valid_until": valid_until,
                "link": data["alternate_url"],
            }
        return 'Error'