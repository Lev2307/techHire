from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic, View

from ..accounts.models import Applicant
from .api_utils import get_vacancies_from_combined_api_sources, get_vacancy_from_api
from .models import Vacancy, SearchHistory, INITIAL_SOURCES

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

class AddVacancyToFavourites(LoginRequiredMixin, View):
    model = Vacancy
    login_url = reverse_lazy("accounts:login")

    def post(self, request, *args, **kwargs):
        vac_api_id = self.kwargs['pk']
        vac_source = request.GET.get('parse_from', '')
        if vac_source in list([i[0] for i in INITIAL_SOURCES]):
            if not self.model.objects.filter(external_id=vac_api_id).exists():
                vacancy_info_from_api = get_vacancy_from_api(vac_api_id, vac_source)
                if vacancy_info_from_api:
                    vac = self.model.objects.create(
                        user=self.request.user,
                        initial_source=vacancy_info_from_api["initial_source"],
                        external_id=vac_api_id,
                        title=vacancy_info_from_api["title"],
                        duties=vacancy_info_from_api["duties"],
                        requirements=vacancy_info_from_api["reqs"],
                        payment_from=vacancy_info_from_api["payment_from"],
                        payment_to=vacancy_info_from_api["payment_to"],
                        experience=vacancy_info_from_api["experience"],
                        education=vacancy_info_from_api["education"],
                        place_of_work=vacancy_info_from_api["place_of_work"],
                        valid_until=vacancy_info_from_api["valid_until"],
                        original_link=vacancy_info_from_api["link"]
                    )
                    vac.save()
                    return HttpResponseRedirect(reverse('vacancies:recom_vacancies'))
                return HttpResponse('Wrong vacancy id!')
            return HttpResponse('Was already added to favorites!')
        return HttpResponse('Wrong parse_from query param')