import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MinValueValidator, MaxValueValidator

from .managers import ApplicantManager

CITY_CHOICES = [
    ('Moscow', 'Москва'),
    ('Saint Petersburg', 'Санкт-Петербург')
]
EXPERIENCE_CHOICES = [
    ('No exp', 'Нет опыта'),
    ('Year', 'От 1 года до 3 лет'),
    ('Three years', 'От 3 до 6 лет'),
    ('Six years', 'Более 6 лет'),
]

class Specialization(models.Model):
    name = models.CharField(max_length=60)

    class Meta:
        verbose_name = 'Specialization'
        verbose_name_plural = 'Specializations'

    def __str__(self):
        return self.name

class Technology(models.Model):
    name = models.CharField(max_length=60)

    class Meta:
        verbose_name = 'Technology'
        verbose_name_plural = 'Technologies'

    def __str__(self):
        return self.name

class ApplicantLinkedTelegram(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(max_length=100)
    user_id = models.BigIntegerField()
    chat_id = models.BigIntegerField()
    date_linked = models.DateTimeField(auto_now_add=True)

class Applicant(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField('Почта', unique=True)
    first_name = models.CharField("Имя", max_length=150)
    last_name = models.CharField("Фамилия", max_length=150)
    city = models.CharField(
        'Ваш город',
        choices=CITY_CHOICES, 
        default=CITY_CHOICES[0][0]
    )
    age = models.PositiveIntegerField(
        'Ваш возраст',
        validators=[
            MinValueValidator(16, message='Ваш возраст должен быть не менее 16 лет.'),
            MaxValueValidator(65, message='Ваш возраст должен быть не более 65 лет.'),
        ],
        default=16
    )
    experience = models.CharField(
        'Ваш опыт работы как IT-специалиста',
        choices=EXPERIENCE_CHOICES,
        default=EXPERIENCE_CHOICES[0][0]
    )
    specializations = models.ManyToManyField(Specialization)
    technologies = models.ManyToManyField(Technology)
    preferred_work_format = models.ManyToManyField('vacancies.WorkFormat')
    linked_telegram = models.OneToOneField(ApplicantLinkedTelegram, on_delete=models.CASCADE, null=True, blank=True)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = ApplicantManager()

    def __str__(self):
        return self.email

