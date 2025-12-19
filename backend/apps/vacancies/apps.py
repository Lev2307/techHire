from django.apps import AppConfig
from django.core.cache import cache

class VacanciesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vacancies'

    def ready(self):
        from .tasks import update_vacancies_for_all_cities
        if not cache.get('update_vacancies_init'):
            update_vacancies_for_all_cities.delay()
            cache.set('update_vacancies_init', True, timeout=None)