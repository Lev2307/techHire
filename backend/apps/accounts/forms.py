from django import forms

from .models import Applicant, Specialization, Technology
from apps.vacancies.models import WorkFormat, WORK_FORMAT_CHOICES

class ApplicantSignUpForm(forms.ModelForm):
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
        fields = ['city', 'experience', 'preferred_work_format', 'specializations', 'technologies']