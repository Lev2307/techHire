from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic, View

from ..accounts.models import Applicant
from .api import get_vacancies_from_combined_api_sources
from .models import Vacancy, SearchHistory

# Create your views here.
class HomeView(generic.TemplateView):
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        user = self.request.user
        if user.is_authenticated:
            return HttpResponseRedirect(reverse('vacancies:recom_vacancies'))
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c['user'] = self.request.user
        return c

class RecommendedVacanciesView(LoginRequiredMixin, View):
    template_name = 'vacancies.html'
    login_url = reverse_lazy("accounts:login")

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class SearchVacanciesView(LoginRequiredMixin, View):
    template_name = 'search.html'
    login_url = reverse_lazy("accounts:login")

    def get(self, request, *args, **kwargs):
        query = request.GET.get('vacancy_name', '')
        salary_from = request.GET.get('payment_from')
        salary_from = int(salary_from) if salary_from else 0
        if query:
            if not SearchHistory.objects.filter(search_query=query).exists():
                new_q = SearchHistory.objects.create(user=self.request.user, search_query=query)
                new_q.save()
            founded_vacancies_by_q = get_vacancies_from_combined_api_sources(query, self.request.user, salary_from)
            return render(request, self.template_name, {'founded_vacancies': founded_vacancies_by_q, 'query': query})
        return HttpResponseRedirect(reverse('vacancies:recom_vacancies'))