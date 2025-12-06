from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Applicant, Specialization, Technology
from apps.vacancies.models import WorkFormat, WORK_FORMAT_CHOICES

class ApplicantCreationForm(UserCreationForm):
    email = forms.EmailField(error_messages={"unique": "Пользователь с такой почтой уже существует!"})
    password1 = forms.CharField(
        label='Пароль',
        strip=False,
        widget=forms.PasswordInput({'autocomplete': 'new-password'})
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        strip=False,
        widget=forms.PasswordInput({'autocomplete': 'new-password'})
    )
    specializations = forms.ModelMultipleChoiceField(
        label='Ваши специализации',
        queryset=Specialization.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': "Выберите хотя бы один пункт из списка специализаций!"}
    )
    technologies = forms.ModelMultipleChoiceField(
        label='Ваши навыки',
        queryset=Technology.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': "Выберите хотя бы один пункт из списка навыков!"}
    )
    preferred_work_format = forms.ModelMultipleChoiceField(
        label='Предпочитаемый формат работы',
        queryset=WorkFormat.objects.exclude(name=WORK_FORMAT_CHOICES[0][1]),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': "Выберите хотя бы один пункт из списка!"}
    )
    class Meta:
        model = Applicant
        fields = ['first_name', 'last_name', 'email', 'city', 'age', 'experience', 'specializations', 'technologies', 'preferred_work_format']

class OwnAuthenticationForm(AuthenticationForm):
    username = forms.EmailField()
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput({'autocomplete': "disabled"})
    )