import urllib.parse

from django.db.models.expressions import RawSQL
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic, View

from apps.accounts.models import Applicant
from .api_utils import get_vacancies_from_combined_api_sources, get_hh_vacancy_data_from_api, get_superjob_vacancy_data_from_api
from .helpers import create_vacancy_model_and_firm_model_instances
from .models import Vacancy, Firm, SearchHistory, INITIAL_SOURCES
from .recommendations import get_recommended_vacancies_by_content

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
    template_name = 'recommended_vacancies.html'
    login_url = reverse_lazy("accounts:login")

    def get(self, request, *args, **kwargs):
        recommended = get_recommended_vacancies_by_content(self.request.user)
        return render(request, self.template_name, {'recommended_vacancies': recommended, 'user': self.request.user})

class SearchVacanciesView(LoginRequiredMixin, View):
    template_name = 'search.html'
    login_url = reverse_lazy("accounts:login")

    def get(self, request, *args, **kwargs):
        query = request.GET.get('query', '')
        payment_from = request.GET.get('payment_from')
        payment_from = int(payment_from) if payment_from else 0
        params_from_form = {
            'query': query,
            'payment_from': payment_from
        }
        if query:
            query = query.lower()
            city_ru_format = Applicant.objects.get(username=self.request.user.username).get_city_display()
            founded_vacancies_by_q = get_vacancies_from_combined_api_sources(city_ru_format, query, payment_from)
            results_count = len(founded_vacancies_by_q)
            if not SearchHistory.objects.filter(user=self.request.user).annotate(is_match=RawSQL("search_query ILIKE '%%' || %s || '%%'", [query])).filter(is_match=True).exists() and results_count > 0:
                new_q = SearchHistory.objects.create(user=self.request.user, search_query=query, results=results_count)
                new_q.save()
            return render(request, self.template_name, {'founded_vacancies': founded_vacancies_by_q, 'url_params': params_from_form})
        return HttpResponseRedirect(reverse('vacancies:recom_vacancies'))

class FavouriteVacanciesList(LoginRequiredMixin, generic.ListView):
    model = Vacancy
    template_name = "favourites.html"
    context_object_name = "favourites"
    login_url = reverse_lazy("accounts:login")

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user, is_archived=False)
    
class AddVacancyToFavourites(LoginRequiredMixin, View):
    model = Vacancy
    login_url = reverse_lazy("accounts:login")

    def post(self, request, *args, **kwargs):
        vac_api_id = self.kwargs['pk']
        vac_source = request.GET.get('parse_from', '')
        url_params = {
            'query': urllib.parse.unquote_plus(request.GET.get('q')),
            'payment_from': request.GET.get('pf')
        }
        applicant = Applicant.objects.get(username=self.request.user.username)
        if vac_source in list([i[0] for i in INITIAL_SOURCES]):
            if not self.model.objects.filter(external_id=vac_api_id).exists():
                if vac_source == INITIAL_SOURCES[0][0]:
                    vacancy_info_from_api = get_superjob_vacancy_data_from_api(vac_api_id)
                else:
                    vacancy_info_from_api = get_hh_vacancy_data_from_api(vac_api_id)
                if vacancy_info_from_api:
                    if self.model.objects.filter(user=self.request.user).count() <= 5: 
                        create_vacancy_model_and_firm_model_instances(
                            self.model,
                            self.request.user,
                            vacancy_info_from_api
                        )
                        return HttpResponseRedirect(reverse('vacancies:search_vacancies', query=url_params))
                    else:
                        if applicant.is_sub:
                            create_vacancy_model_and_firm_model_instances(
                                self.model,
                                self.request.user,
                                vacancy_info_from_api
                            )
                        return HttpResponse('Вы должны быть сабом, чтобы добавлять в избранное больше 5-ти вакансий!')
                return HttpResponse('Неправильное id вакансии!')
            return HttpResponse('Вакансия уже была добалена в избранное!')
        return HttpResponse('Неправильный параметр parse_from')
    
class RemoveVacancyFromFavorites(LoginRequiredMixin, generic.DeleteView):
    model = Vacancy
    login_url = reverse_lazy("accounts:login")

    def get_object(self):
        return self.model.objects.get(external_id=self.kwargs['pk'])
    
    def get_success_url(self):
        if self.request.GET.get('q') != None and self.request.GET.get('pf') != None:
            url_params = {
                'query': urllib.parse.unquote_plus(self.request.GET.get('q')),
                'payment_from': self.request.GET.get('pf')
            }
            return reverse_lazy("vacancies:search_vacancies", query=url_params)
        else:
            return reverse_lazy("vacancies:favourite_vacancies")
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if self.request.user.is_authenticated:
            if obj.user != self.request.user:
                return self.handle_vacancy_not_found()
        else:
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def handle_vacancy_not_found(self):
        return HttpResponseRedirect(reverse("vacancies:recom_vacancies"))