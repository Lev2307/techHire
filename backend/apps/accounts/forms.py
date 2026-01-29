from django import forms
from django.db.models import Q


from .models import Applicant, Specialization, Technology
from apps.vacancies.models import WorkFormat, WORK_FORMAT_CHOICES

class ApplicantForm(forms.ModelForm):
    specializations = forms.ModelMultipleChoiceField(
        label='Ваши специализации',
        queryset=Specialization.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': "Выберите хотя бы один пункт из списка специализаций!"}
    )
    technologies = forms.ModelMultipleChoiceField(
        label='Ваши навыки',
        queryset=Technology.objects.filter(creator=None, is_approved=True),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': "Выберите хотя бы один пункт из списка навыков!"}
    )
    preferred_work_formats = forms.ModelMultipleChoiceField(
        label='Предпочитаемый формат работы',
        queryset=WorkFormat.objects.exclude(name=WORK_FORMAT_CHOICES[0][1]),
        widget=forms.CheckboxSelectMultiple,
        error_messages={'required': "Выберите хотя бы один пункт из списка!"}
    )
    class Meta:
        model = Applicant
        fields = ['city', 'experience', 'preferred_work_formats', 'specializations', 'technologies']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Передаем юзера во вьюхе
        super().__init__(*args, **kwargs)
        if user:
            self.fields['technologies'].queryset = Technology.objects.filter(
                Q(is_approved=True) | Q(creator=user)
            )

class TechnologyForm(forms.ModelForm):
    name = forms.CharField(
        label="",
        max_length=60,
        required=True,
        widget=forms.TextInput(attrs={
            'placeholder': 'Введите название инструмента', 
            'autocomplete': 'off',
            'style': 'width: 250px; height: 20px;'
        }),
        help_text='Пример инструментов: Python, Django, Next.js и т.д.'
    )
    class Meta:
        model = Technology
        fields = ['name']

    def clean(self):
        tech_name = self.cleaned_data.get("name")
        all_approved_techs = list(Technology.objects.filter(is_approved=True).values_list('name', flat=True))
        all_approved_techs = [i.lower() for i in all_approved_techs]
        for tech in all_approved_techs:
            if tech_name.lower() in tech:
                raise forms.ValidationError('Название инструмента не должно совпадать с названием уже существующего инструмента!!!')
            