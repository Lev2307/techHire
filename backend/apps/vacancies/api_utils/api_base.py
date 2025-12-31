from .api_hh import get_vacancies_from_headhunter_source
from .api_superjob import get_vacancies_from_superjob_source
from .constants import NUMBER_OF_VACANCIES_TO_BE_FOUND

def get_vacancies_from_combined_api_sources(applicant_city_ru_format: str, query="", salary_from=0, number_of_vacancies=NUMBER_OF_VACANCIES_TO_BE_FOUND, are_for_recommendations=False) -> list:
    hh_pages_count = 20 if are_for_recommendations else 1
    superjob_pages_count = 4 if are_for_recommendations else 1
    headhunter_vacancies = get_vacancies_from_headhunter_source(
        query, 
        applicant_city_ru_format, 
        salary_from, 
        hh_pages_count,
        are_for_recommendations,
        number_of_vacancies,
    )
    superjob_vacancies = get_vacancies_from_superjob_source(
        query,
        applicant_city_ru_format, 
        salary_from, 
        superjob_pages_count,
        are_for_recommendations,
        number_of_vacancies
    )

    return headhunter_vacancies + superjob_vacancies
