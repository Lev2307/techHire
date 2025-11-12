from celery import shared_task


@shared_task
def make_vacancy_archived_task(vacancy_id):
    ''' Функция, которая меняет статус у избранной вакансии с действительной на заархивированную '''
    from .models import Vacancy
    vac = Vacancy.objects.filter(id=vacancy_id)
    if vac.exists():
        vac.update(is_archived=True)
    else:
        print('Vacancy was deleted before making it archived!')

