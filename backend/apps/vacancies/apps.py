from django.apps import AppConfig


class VacanciesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vacancies'

    def ready(self):
        from .tasks import update_vacancies_for_all_cities
        update_vacancies_for_all_cities.delay()