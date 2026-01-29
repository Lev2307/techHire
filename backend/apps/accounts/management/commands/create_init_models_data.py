from django.core.management.base import BaseCommand
from apps.vacancies.models import WorkFormat, WORK_FORMAT_CHOICES
from apps.accounts.models import Specialization, Technology
from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST

class Command(BaseCommand):
    help = 'Создает данные для специализаций, технологий и форматов работы, если они отсутствуют.'

    def handle(self, *args, **kwargs):
        for name in SPECIALIZATIONS_LIST:
            obj, created = Specialization.objects.get_or_create(name=name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Специализация "{name}" создана'))

        for name in TECHNOLOGIES_LIST:
            obj, created = Technology.objects.get_or_create(
                name=name, 
                defaults={'is_approved': True}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Технология "{name}" создана'))

        for eng_name, ru_name in WORK_FORMAT_CHOICES:
            obj, created = WorkFormat.objects.get_or_create(
                name_eng=eng_name,
                defaults={'name': ru_name}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Формат работы "{ru_name}" создан'))

        self.stdout.write(self.style.SUCCESS('Синхронизация первичных моделей завершена!'))