from celery import shared_task

from django.core.cache import cache

from config.settings import RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS
from apps.accounts.models import Applicant, CITY_CHOICES

@shared_task
def make_vacancy_archived_task(vacancy_id):
    ''' Функция, которая меняет статус у избранной вакансии с действительной на заархивированную '''
    from .models import Vacancy
    vac = Vacancy.objects.filter(id=vacancy_id)
    if vac.exists():
        vac.update(is_archived=True)
    else:
        print('Vacancy was deleted before making it archived!')

@shared_task
def update_vacancies_for_all_cities():
    from .api_utils import get_vacancies_from_combined_api_sources
    cities = list(Applicant.objects.values_list('city', flat=True).distinct())
    cities_ru = []
    for i in range(len(cities)):
        if CITY_CHOICES[i][0] == cities[i]:
            cities_ru.append(CITY_CHOICES[i][1])
    for city in cities_ru:
        vacancies = get_vacancies_from_combined_api_sources(city, salary_from=0, number_of_vacancies=100, pages_count=6, are_for_recommendations=True)
        cache.set(f'STORED_VACANCIES_FOR_RECOMMENDATIONS_USER_{city}', vacancies, timeout=RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS*3600)
        print('her automatically')
        print(f"vacancies for city {city}")