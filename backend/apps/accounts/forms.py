from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm

from .models import Applicant, Specialization, Technology

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
    class Meta:
        model = Applicant
        fields = ['first_name', 'last_name', 'email', 'city', 'gender', 'age', 'experience', 'specializations', 'technologies']


class OwnAuthenticationForm(AuthenticationForm):
    username = forms.EmailField()
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput()
    )