from django.http import HttpResponse
from django.views import generic
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy

from config import settings
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["bot_token"] = settings.TELEGRAM_BOT_TOKEN
        context["redirect_url"] = settings.DOMAIN_FOR_TUNELLING + 'auth/telegram'
        return context

def telegram_auth(request):
    return HttpResponse('Прива')

# cloudflared tunnel run techhiretunnel
# login from google unfo