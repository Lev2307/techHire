import uuid

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
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
    user_id = models.BigIntegerField()
    chat_id = models.BigIntegerField(null=True, blank=True)
    date_linked = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user_id)

class Applicant(AbstractBaseUser, PermissionsMixin):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = models.CharField(
        'Имя пользователя',
        max_length=32,
        unique=True,
        validators=[UnicodeUsernameValidator()],
        error_messages={
            'unique': 'Пользователь с таким именем уже существует'
        }
    )
    first_name = models.CharField(
        'Имя',
        max_length=64
    )
    email = models.EmailField(
        'Почта', 
        unique=True,
        null=True,
        blank=True
    ) # пока что будет пустым, потом может быть сделаю уведы через почту
    city = models.CharField(
        'Ваш город',
        choices=CITY_CHOICES, 
        default=CITY_CHOICES[0][0]
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
    is_sub = models.BooleanField(default=False) # есть ли подписка у аппликанта (пока будет просто как флаг, потом мб сделаю платёжную систему для неё)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    objects = ApplicantManager()

    def __str__(self):
        return self.username

