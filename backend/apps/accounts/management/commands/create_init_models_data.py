from django.core.management.base import BaseCommand

from apps.vacancies.models import WorkFormat, WORK_FORMAT_CHOICES
from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST

from ...models import Specialization, Technology


class Command(BaseCommand):
    help = 'Создаёт при первом запуске проекта модели специализаций и инструментов разработки.'

    def handle(self, *args, **options):
        if not (Specialization.objects.exists() and Technology.objects.exists()):
            for s in SPECIALIZATIONS_LIST:
                spec = Specialization.objects.create(name=s)
                spec.save()
            for t in TECHNOLOGIES_LIST:
                technology = Technology.objects.create(name=t, is_approved=True)
                technology.save()
            print('Начальные данные для специализаций и инструментов созданы!')
        else:
            print('Модели специализаций и инструментов уже были созданы ))')

        if not WorkFormat.objects.exists():
            for wf in WORK_FORMAT_CHOICES:
                work_format = WorkFormat.objects.create(name_eng=wf[0], name=wf[1])
                work_format.save()
            print('Начальные данные для формата работы созданы!')
        else:
            print('Начальные данные для формата работы уже были созданы ))')