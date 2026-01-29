from celery import shared_task

from django.core.cache import cache
from django.urls import reverse

from config.settings import RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS
from apps.accounts.models import Applicant, CITY_CHOICES

@shared_task
def make_vacancy_archived_task(vacancy_id):
    ''' Функция, которая меняет статус у избранной вакансии с действительной на заархивированную '''
    from .models import Vacancy
    vac = Vacancy.objects.filter(id=vacancy_id).first()
    print(vac.valid_until)
    if vac:
        vac.is_archived = True
        vac.save()
    else:
        print('Vacancy was deleted before making it archived!')

@shared_task
def process_recoms_for_single_user(applicant_id):
    from apps.accounts.tasks import send_telegram_message
    from .recommendations.base import get_recommended_vacancies_by_content
    from .helpers import prepare_vacancy_for_telegram_message

    applicant = Applicant.objects.get(id=applicant_id)
    # print(f"Task: process_recoms_for_single_user - {applicant}")
    new_list_recommendations, new_list_of_external_ids_recommendations = get_recommended_vacancies_by_content(applicant, for_auto_updating_vacancies=True) # получаю новые рекомендованные вакансии (точнее их список и список из external_id вакансий), исходя из нового сбора вакансий
    previous_list_of_external_ids_recom_vacancies = cache.get(f"LATEST_LIST_RECOMMENDATIONS_EXTERNAL_IDS_FOR_USER_{applicant.username}", default=new_list_of_external_ids_recommendations) # получаю из кэша последние рекомендованные вакансии пользователя

    # извлечение новых вакансий (сравнение предыдущих рекомендаций и новых только что сгенерированных) + их отправка только в случае, если пользователь включил уведы и привязал тг к боту
    if applicant.notifications_enabled:
        if applicant.linked_telegram and applicant.linked_telegram.is_active:
            new_recommended_vacancies_external_ids = list(set(new_list_of_external_ids_recommendations) - set(previous_list_of_external_ids_recom_vacancies))
            new_recommended_vacancies = []
            for recom in new_list_recommendations:
                for ext_id in new_recommended_vacancies_external_ids:
                    if recom.get("external_id") == ext_id:
                        new_recommended_vacancies.append(recom)
            # print(f"process_recoms_for_single_user - {len(new_recommended_vacancies)}")
            for new_vac in new_recommended_vacancies:
                vacancy_text_for_telegram = prepare_vacancy_for_telegram_message(new_vac)
                send_telegram_message.delay(vacancy_text_for_telegram, applicant_id)

    # пересохраняю список новых рекомендованных вакансий (их external_ids), - на всякий случай, если пользователь не будет пользоваться приложением до следующего вызова таски auto_updating_vacancies
    cache.set(f"LATEST_LIST_RECOMMENDATIONS_EXTERNAL_IDS_FOR_USER_{applicant.username}", new_list_of_external_ids_recommendations, timeout=None) 
    print(cache.get(f"LATEST_LIST_RECOMMENDATIONS_EXTERNAL_IDS_FOR_USER_{applicant.username}"))

@shared_task
def auto_updating_vacancies():
    '''Таска сбора вакансий для всех существующих городов в базе, сохранение их в кэш и обновление рекомендованных вакансий для всех пользователей (обновление кэша + отправка уведомлений, если пользователь включил их)'''
    from .api_utils import get_vacancies_from_combined_api_sources
    cities_ru = [i[1] for i in CITY_CHOICES]

    for city in cities_ru:
        print(city)
        vacancies = get_vacancies_from_combined_api_sources(city, salary_from=0, number_of_vacancies=100, are_for_recommendations=True)
        cache.set(f'STORED_VACANCIES_FOR_RECOMMENDATIONS_CITY_{city}', vacancies, timeout=RECOMMENDED_VACANCIES_LIFETIME_IN_HOURS*3600)
        print(f"vacancies for city {city}")

    applicant_ids = Applicant.objects.values_list('id', flat=True)
    for app_id in applicant_ids:
        process_recoms_for_single_user.delay(app_id)