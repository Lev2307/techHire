from django.apps import AppConfig
from django.core.cache import cache

class VacanciesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vacancies'

    def ready(self):
        from .tasks import auto_updating_vacancies
        if not cache.get('auto_updating_vacancies_init'):
            auto_updating_vacancies.delay()
            cache.set('auto_updating_vacancies_init', True, timeout=None)