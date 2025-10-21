from django.apps import apps

from django.core.management.base import BaseCommand
from ...models import Specialization, Technology

from config.settings import SPECIALIZATIONS_LIST, TECHNOLOGIES_LIST

class Command(BaseCommand):
    help = 'Создаёт при первом запуске проекта модели специализаций и инструментов разработки.'

    def handle(self, *args, **options):
        if not (Specialization.objects.exists() and Technology.objects.exists()):
            for s in range(len(SPECIALIZATIONS_LIST)):
                spec = Specialization.objects.create(name=SPECIALIZATIONS_LIST[s])
                spec.save()
            for t in range(len(TECHNOLOGIES_LIST)):
                technology = Technology.objects.create(name=TECHNOLOGIES_LIST[t])
                technology.save()
            self.stdout.write(self.style.SUCCESS('Начальные данные созданы!'))
        else:
            self.stdout.write(self.style.SUCCESS('Модели уже были созданы )'))
