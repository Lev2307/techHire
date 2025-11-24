
from apps.accounts.models import Applicant
from .api_hh import get_vacancies_from_headhunter_source
from .api_superjob import get_vacancies_from_superjob_source
from .constants import NUMBER_OF_VACANCIES_TO_BE_FOUND

def get_vacancies_from_combined_api_sources(query: str, user: Applicant, salary_from: int) -> dict:
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from, NUMBER_OF_VACANCIES_TO_BE_FOUND)
    headhunter_vacancies = get_vacancies_from_headhunter_source(query, user, salary_from, NUMBER_OF_VACANCIES_TO_BE_FOUND-len(superjob_vacancies))

    return headhunter_vacancies + superjob_vacancies
