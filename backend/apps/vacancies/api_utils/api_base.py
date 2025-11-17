
from apps.accounts.models import Applicant
from .api_hh import get_vacancies_from_headhunter_source
from .api_superjob import get_vacancies_from_superjob_source

def get_vacancies_from_combined_api_sources(query: str, user: Applicant, salary_from: int) -> dict:
    headhunter_vacancies = get_vacancies_from_headhunter_source(query, user, salary_from)
    superjob_vacancies = get_vacancies_from_superjob_source(query, user, salary_from)

    return headhunter_vacancies + superjob_vacancies
