import hashlib
import hmac
import time

from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views import generic

from rest_framework.authtoken.models import Token

from config import settings
from .forms import ApplicantForm, TechnologyForm
from .models import Applicant, ApplicantLinkedTelegram, Technology

    
class ProfileView(LoginRequiredMixin, generic.DetailView):
    model = Applicant
    template_name = 'profile/profile.html'
    login_url = reverse_lazy('accounts:login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user'] = self.get_object()
        context["add_technology_form"] = TechnologyForm
        context['applicant_created_tecchnologies_options'] = Technology.objects.filter(creator=self.get_object()).order_by("-created_at")
        return context

    def get_object(self, queryset=None):
        return self.model.objects.get(username=self.request.user.username)
    
class EditProfileView(LoginRequiredMixin, generic.UpdateView):
    model = Applicant
    form_class = ApplicantForm
    template_name = 'profile/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = reverse_lazy('accounts:login')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_object(self, queryset=None):
        return self.model.objects.get(username=self.request.user.username)

class AddOwnTechnologyToApplicantView(LoginRequiredMixin, generic.CreateView):
    model = Technology
    form_class = TechnologyForm
    template_name = 'profile/add_own_technology.html'
    success_url = reverse_lazy('accounts:profile')
    login_url = reverse_lazy('accounts:login')

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()
        self.request.user.technologies.add(self.object)

        return HttpResponseRedirect(self.get_success_url())
    
class EditOwnTechnologyFromApplicantView(LoginRequiredMixin, generic.UpdateView):
    model = Technology
    form_class = TechnologyForm
    template_name = 'profile/edit_own_technology.html'
    success_url = reverse_lazy("accounts:profile")
    login_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.creator != self.request.user: # редактировать может только создатель варианта
            return HttpResponseRedirect(reverse("accounts:profile"))
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tech"] = self.get_object()
        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.save()

        return HttpResponseRedirect(self.get_success_url())
    
@login_required
def delete_own_technology_from_applicant_view(request, pk):
    if request.method == "POST":
        obj = get_object_or_404(Technology, pk=pk)
        if obj.creator != request.user:
            return HttpResponseRedirect(reverse("accounts:profile"))
        obj.delete()
        return HttpResponseRedirect(reverse("accounts:profile"))
    
class PendingTechnologyListView(PermissionRequiredMixin, generic.ListView):
    model = Technology
    template_name = 'admin/moderation_list.html'
    permission_required = 'is_superuser'
    context_object_name = 'technologies'
    login_url = reverse_lazy("accounts:profile")

    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Technology.objects.filter(is_approved=False).order_by("-created_at")

    def post(self, request, *args, **kwargs):
        tech_id = request.POST.get('tech_id')
        action = request.POST.get('action')
        tech = get_object_or_404(Technology, id=tech_id)
        creator = get_object_or_404(Applicant, username=tech.creator.username)

        if action == 'approve':
            tech.is_approved = True
            tech.save() # статус у технологии - approved
            if not creator.technologies.filter(name=tech.name).exists(): # автоматически присваивается к пользователю после модерации
                creator.technologies.add(tech)
                creator.save()
        elif action == 'delete':
            tech.delete()

        return HttpResponseRedirect(reverse('accounts:pending_technologies'))

class LoginView(generic.View):
    template_name = 'login.html'

    def get(self, request):
        return render(request, self.template_name, {'bot_token_digits': settings.TELEGRAM_BOT_ID})

def sign_up_view(request):
    if request.method == "POST":
        user_data = request.session['tg_user_data']
        if not user_data:
            return HttpResponseRedirect(reverse('accounts:login'))
        # повторные проверки, но уже для POST запроса
        # проверка на валидность времени
        if time.time() - int(user_data.get('auth_date')) > 300:
            return HttpResponseRedirect(reverse('accounts:login'))
        # проверка хэшей
        if user_data.get('hash') != '' and user_data.get('hash') == user_data.get('secret'):
            form = ApplicantForm(request.POST)
            if form.is_valid():
                # Linked Telegram instance
                linked_telega = ApplicantLinkedTelegram.objects.create(
                    user_id=user_data.get('id')
                )
                # creating Applicant instance
                telegram_username = user_data.get('username')
                telegram_first_name = user_data.get('first_name')
                applicant = form.save(commit=False)
                applicant.username = telegram_username
                applicant.first_name = telegram_first_name
                applicant.linked_telegram = linked_telega
                applicant.save()
                form.save_m2m()

                login(request, applicant)
                # token = Token.objects.create(user=applicant)
                # linked_telega.auth_token = token.key
                # linked_telega.save()

                del request.session['tg_user_data']
                return HttpResponseRedirect(reverse('accounts:profile'))
        
def telegram_auth(request):
    if request.method == "GET":
        # decode tgAuthResult to telegram user provided data
        if not request.GET:
            return render(request, 'telegram_auth_js_loader.html')
        data = request.GET

        # checking url validity
        if time.time() - int(data.get('auth_date')) > 300: # 5 minutes max
            return HttpResponse('Ссылка устарела!!!')

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
                'secret': secret,
                'hash': hash
            }
            request.session['tg_user_data'] = user_data
            link = ApplicantLinkedTelegram.objects.filter(user_id=user_data["id"]).first()
            if link:
                login(request, link.applicant)
                return HttpResponseRedirect(reverse('accounts:profile'))
            else:
                form = ApplicantForm()
                return render(request, 'signup.html', {'form': form})
        else:
            return HttpResponseRedirect(reverse('accounts:login'))
    else:
        return HttpResponseRedirect(reverse('accounts:login'))
    
# cloudflared tunnel run techhiretunnel
# login from google unfo