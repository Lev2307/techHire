import uuid

from django.db import models

from ..accounts.models import Applicant, EXPERIENCE_CHOICES

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
PLACE_OF_WORK_CHOICES = [
    ('office', 'Очная'),
    ('remote', 'Удалённая'),
    ('not specified', 'Не имеет значения')
]

class Firm(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Название', max_length=50)
    activity = models.TextField('Род деятельности', max_length=150)
    address = models.CharField('Адрес', max_length=100)
    link = models.URLField('Ссылка', max_length=50)

    def __str__(self):
        return self.name

class Vacancy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    initial_source = models.CharField('Источник', choices=INITIAL_SOURCES, default=INITIAL_SOURCES[0][0])
    external_id = models.PositiveIntegerField()
    title = models.CharField('Название', max_length=100)
    duties = models.TextField('Задачи', max_length=1500)
    requirements = models.TextField('Требования', max_length=2000)
    payment_from = models.PositiveIntegerField('Зп от', blank=True, null=True)
    payment_to = models.PositiveIntegerField('Зп до', blank=True, null=True)
    experience = models.CharField('Опыт', choices=EXPERIENCE_CHOICES, default=EXPERIENCE_CHOICES[0][0])
    education = models.CharField('Образование', choices=EDUCATION_CHOICES, default=EDUCATION_CHOICES[0][0])
    place_of_work = models.CharField('Тип работы', choices=PLACE_OF_WORK_CHOICES, default=PLACE_OF_WORK_CHOICES[0][0])
    valid_until = models.DateTimeField('Вакансия действительна до')
    original_link = models.URLField('Ссылка на вакансию', max_length=150) 
    date_added = models.DateTimeField('Время добавления', auto_now=True)
    firm = models.ForeignKey(Firm, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Vacancies'
        
    def __str__(self):
        return self.title

class SearchHistory(models.Model):
    user = models.ForeignKey(Applicant, on_delete=models.CASCADE)
    search_query = models.CharField(max_length=70)
    results = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Search Histories'
    
    def __str__(self):
        return self.search_query