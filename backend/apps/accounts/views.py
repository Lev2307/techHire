import hashlib
import hmac
import time

from django.contrib.auth import login
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from config import settings
from .forms import ApplicantSignUpForm
from .models import Applicant, ApplicantLinkedTelegram

class LoginView(generic.View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name, {'bot_token_digits': settings.TELEGRAM_BOT_ID})
    
def sign_up_view(request):
    if request.method == "POST":
        form = ApplicantSignUpForm(request.POST)
        if form.is_valid():
            # Linked Telegram instance
            linked_telega = ApplicantLinkedTelegram.objects.create(
                user_id=request.POST.get('telega_id')
            )

            # creating Applicant instance
            telegram_username = request.POST.get('telega_username')
            telegram_first_name = request.POST.get('telega_first_name')
            applicant = form.save(commit=False)
            applicant.username = telegram_username
            applicant.first_name = telegram_first_name
            applicant.linked_telegram = linked_telega
            applicant.save()
            form.save_m2m()

            login(request, applicant)
            return HttpResponseRedirect(reverse('homepage'))
        
def telegram_auth(request):
    if request.method == "GET":
        # decode tgAuthResult to telegram user provided data
        if not request.GET:
            return render(request, 'telegram_auth_js_loader.html')
        data = request.GET

        # checking url validity
        if time.time() - int(data.get('auth_date')) > 300: # 5 minutes max
            return HttpResponse('Ссылка устарела иди обратно')

        # getting hash and compare to own generated hash which depends on tg data and bot token
        hash = data.get('hash')
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])
        secret = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()

        if secret == hash:
            user_data = {
                'id': data.get('id'),
                'username': data.get('username'),
                'first_name': data.get('first_name'),
                'auth_date': data.get('auth_date'),
            }
            if Applicant.objects.filter(username=user_data["username"]).exists():
                applicant = Applicant.objects.get(username=user_data["username"])
                login(request, applicant)
                return HttpResponseRedirect(reverse('homepage'))
            else:
                form = ApplicantSignUpForm()
                return render(request, 'signup.html', {'user_data': user_data, 'form': form})
        else:
            return HttpResponseRedirect(reverse('accounts:login'))
    else:
        return HttpResponseRedirect(reverse('accounts:login'))
# cloudflared tunnel run techhiretunnel
# login from google unfo