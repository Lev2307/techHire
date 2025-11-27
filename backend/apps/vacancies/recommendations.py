

from apps.accounts.models import Applicant
from .api_utils.api_base import get_vacancies_from_combined_api_sources
from .helpers import (
    get_applicant_criterias_for_filtering_vacancies,
    get_applicant_favourite_vacancies_info_for_filtering_vacancies,
    get_applicant_search_history_info_for_filtering_vacancies
)
from .models import Vacancy, SearchHistory
def filter_vacancies_by_content(user: Applicant) -> list:
    '''Генерирует вакансии на основе алгоритма контентной фильтрации'''
    applicant_data = get_applicant_criterias_for_filtering_vacancies(user)
    applicant_fav_vacancies_data = get_applicant_favourite_vacancies_info_for_filtering_vacancies(Vacancy.objects.filter(user=user))
    applicant_search_histories = get_applicant_search_history_info_for_filtering_vacancies(SearchHistory.objects.filter(user=user))


