import uuid

from django.db import models
from django.utils import timezone

from ..accounts.models import Applicant, EXPERIENCE_CHOICES
from .tasks import make_vacancy_archived_task

INITIAL_SOURCES = [
    ('SuperJob', 'SuperJob'),
    ('HH', 'hh.ru')
]
EDUCATION_CHOICES = [
    ('not specified', 'Не имеет значения'),
    ('Student', 'Учащийся'),
    ('Higher', 'Высшее'),
    ('Incomplete_higher', 'Неполное высшее'),
    ('Secondary_special', 'Средне-специальное'),
    ('Secondary', 'Среднее'),
]

WORK_FORMAT_CHOICES = [
    ('Not specified', 'Не имеет значения'),
    ('ON_SITE', 'Очная'),
    ('REMOTE', 'Удалённая'),
    ('HYBRID', 'Гибрид')
]

class WorkFormat(models.Model):
    name = models.CharField(max_length=50)
    name_eng = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class Firm(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Название', max_length=100)
    address = models.CharField('Адрес', max_length=150)
    link = models.URLField('Ссылка', max_length=100)

    def __str__(self):
        return self.name

class Vacancy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    initial_source = models.CharField('Источник', choices=INITIAL_SOURCES, default=INITIAL_SOURCES[0][0])
    external_id = models.PositiveIntegerField(unique=True)
    title = models.CharField('Название', max_length=100)
    duties = models.TextField('Задачи', max_length=1500)
    requirements = models.TextField('Требования', max_length=2000)
    working_conditions = models.TextField('Условия работы', max_length=1500)
    payment_from = models.PositiveIntegerField('Зп от', blank=True, null=True)
    payment_to = models.PositiveIntegerField('Зп до', blank=True, null=True)
    currency = models.CharField("Валюта", max_length=3)
    experience = models.CharField('Опыт', choices=EXPERIENCE_CHOICES, default=EXPERIENCE_CHOICES[0][0])
    education = models.CharField('Образование', choices=EDUCATION_CHOICES, default=EDUCATION_CHOICES[0][0])
    work_formats = models.ManyToManyField(WorkFormat)
    date_published = models.DateTimeField('Дата опубликования вакансии')
    valid_until = models.DateTimeField('Вакансия действительна до')
    original_link = models.URLField('Ссылка на вакансию', max_length=150) 
    date_added = models.DateTimeField('Время добавления', auto_now=True)
    is_archived = models.BooleanField(default=False) # статус действительности вакансии (возможно потом сделаю просто удаление её, если она уже не является ликвидной )
    firm = models.ForeignKey(Firm, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Vacancies'
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        make_vacancy_archived_task.apply_async(args=(self.id, ), eta=self.valid_until)
        super().save(*args, **kwargs)

class SearchHistory(models.Model):
    user = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    search_query = models.CharField(max_length=70)
    results = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Search Histories'
    
    def __str__(self):
        return self.search_query