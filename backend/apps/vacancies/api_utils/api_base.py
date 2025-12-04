
from apps.accounts.models import Applicant
from .api_hh import get_vacancies_from_headhunter_source
from .api_superjob import get_vacancies_from_superjob_source
from .constants import NUMBER_OF_VACANCIES_TO_BE_FOUND, NOT_FOUND_DUTIES, NOT_FOUND_REQS

def get_vacancies_from_combined_api_sources(user: Applicant, query="",  salary_from=0, number_of_vacancies=NUMBER_OF_VACANCIES_TO_BE_FOUND) -> list:
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from, number_of_vacancies)
    headhunter_vacancies = get_vacancies_from_headhunter_source(query, user, salary_from, number_of_vacancies)

    return headhunter_vacancies + superjob_vacancies

def get_vacancies_from_combined_api_sources_with_requirements_or_duties_fullfilled_both(user: Applicant, num: int) -> list:
    vacancies = get_vacancies_from_combined_api_sources(user, number_of_vacancies=num)
    for vac in vacancies:
        if vac["duties"] == NOT_FOUND_DUTIES and vac["requirements"] == NOT_FOUND_REQS:
            vacancies.remove(vac)
    return vacancies