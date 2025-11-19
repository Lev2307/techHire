import urllib.parse

from django.db.models.expressions import RawSQL
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic, View

from .models import Vacancy, Firm, SearchHistory, INITIAL_SOURCES
from .api_utils import get_vacancies_from_combined_api_sources, get_hh_vacancy_data_from_api, get_superjob_vacancy_data_from_api

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
        query = request.GET.get('query', '')
        payment_from = request.GET.get('payment_from')
        payment_from = int(payment_from) if payment_from else 0
        params_from_form = {
            'query': query,
            'payment_from': payment_from
        }
        if query:
            query = query.lower()
            founded_vacancies_by_q = get_vacancies_from_combined_api_sources(query, self.request.user, payment_from)
            results_count = len(founded_vacancies_by_q)
            if not SearchHistory.objects.filter(user=self.request.user).annotate(is_match=RawSQL("(%s ILIKE '%%' || search_query || '%%') OR (search_query ILIKE '%%' || %s || '%%')", [query, query])).filter(is_match=True).exists() and results_count > 0:
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
            'query': urllib.parse.quote_plus(request.GET.get('q')),
            'payment_from': request.GET.get('pf')
        }
        if vac_source in list([i[0] for i in INITIAL_SOURCES]):
            if not self.model.objects.filter(external_id=vac_api_id).exists():
                if vac_source == INITIAL_SOURCES[0][0]:
                    vacancy_info_from_api = get_superjob_vacancy_data_from_api(vac_api_id)
                else:
                    vacancy_info_from_api = get_hh_vacancy_data_from_api(vac_api_id)
                if vacancy_info_from_api:
                    # creating firm if not existed
                    if not Firm.objects.filter(name=vacancy_info_from_api["employer"]["name"]).exists():
                        firm = Firm.objects.create(
                            name=vacancy_info_from_api["employer"]["name"],
                            address=vacancy_info_from_api["employer"]["address"],
                            link=vacancy_info_from_api["employer"]["alternate_url"],
                        )
                        firm.save()
                    else:
                        firm = Firm.objects.get(name=vacancy_info_from_api["employer"]["name"])
                    # creating fav vacancy
                    vac = self.model.objects.create(
                        user=self.request.user,
                        initial_source=vacancy_info_from_api["initial_source"],
                        external_id=vac_api_id,
                        title=vacancy_info_from_api["title"],
                        duties=vacancy_info_from_api["duties"],
                        requirements=vacancy_info_from_api["requirements"],
                        working_conditions=vacancy_info_from_api["working_conditions"],
                        payment_from=vacancy_info_from_api["payment"]["payment_from"],
                        payment_to=vacancy_info_from_api["payment"]["payment_to"],
                        currency=vacancy_info_from_api["payment"]["currency"],
                        experience=vacancy_info_from_api["experience"],
                        education=vacancy_info_from_api["education"],
                        date_published=vacancy_info_from_api["date_published"],
                        valid_until=vacancy_info_from_api["valid_until"],
                        original_link=vacancy_info_from_api["original_link"],
                        firm=firm
                    )
                    vac.work_format.add(*vacancy_info_from_api["work_formats"])
                    return HttpResponseRedirect(reverse('vacancies:search_vacancies', query=url_params))
                return HttpResponse('Wrong vacancy id!')
            return HttpResponse('Was already added to favorites!')
        return HttpResponse('Wrong parse_from query param')
    
class RemoveVacancyFromFavorites(LoginRequiredMixin, generic.DeleteView):
    model = Vacancy
    login_url = reverse_lazy("accounts:login")

    def get_object(self):
        return self.model.objects.get(external_id=self.kwargs['pk'])
    
    def get_success_url(self):
        if self.request.GET.get('q') != None and self.request.GET.get('pf') != None:
            url_params = {
                'query': urllib.parse.quote_plus(self.request.GET.get('q')),
                'payment_from': self.request.GET.get('pf')
            }
            return reverse_lazy("vacancies:search_vacancies", query=url_params)
        else:
            return reverse_lazy("vacancies:favourite_vacancies")
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            return self.handle_vacancy_not_found()
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect(self.get_success_url())

    def handle_vacancy_not_found(self):
        return HttpResponseRedirect(reverse("vacancies:recom_vacancies"))