from django.shortcuts import render
from django.views import generic
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from .forms import ApplicantCreationForm, OwnAuthenticationForm
from .models import Applicant

class RegisterApplicantView(generic.CreateView):
    model = Applicant
    form_class = ApplicantCreationForm
    template_name = 'registration.html'
    success_url = reverse_lazy('accounts:login')

class LoginView(LoginView):
    template_name = 'login.html'
    form_class = OwnAuthenticationForm

    