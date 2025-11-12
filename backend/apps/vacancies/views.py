import urllib.parse

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.urls import reverse, reverse_lazy
from django.views import generic, View

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
        payment_from = request.GET.get('payment_from')
        payment_from = int(payment_from) if payment_from else 0
        params_from_form = {
            'query': query,
            'payment_from': payment_from
        }
        if query:
            founded_vacancies_by_q = get_vacancies_from_combined_api_sources(query, self.request.user, payment_from)
            res = len(founded_vacancies_by_q)
            if not SearchHistory.objects.filter(search_query__icontains=query).exists() and res > 0:
                new_q = SearchHistory.objects.create(user=self.request.user, search_query=query, results=res)
                new_q.save()
            return render(request, self.template_name, {'founded_vacancies': founded_vacancies_by_q, 'url_params': params_from_form})
        return HttpResponseRedirect(reverse('vacancies:recom_vacancies'))

class FavouriteVacanciesList(LoginRequiredMixin, generic.ListView):
    model = Vacancy
    template_name = "favourites.html"
    context_object_name = "favourites"

    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user, is_archived=False)
    
class AddVacancyToFavourites(LoginRequiredMixin, View):
    model = Vacancy
    login_url = reverse_lazy("accounts:login")

    def post(self, request, *args, **kwargs):
        vac_api_id = self.kwargs['pk']
        vac_source = request.GET.get('parse_from', '')
        url_params = {
            'vacancy_name': urllib.parse.quote_plus(request.GET.get('q')),
            'payment_from': request.GET.get('pf')
        }
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
                        working_conditions=vacancy_info_from_api["working_conditions"],
                        payment_from=vacancy_info_from_api["payment_from"],
                        payment_to=vacancy_info_from_api["payment_to"],
                        currency=vacancy_info_from_api["currency"],
                        experience=vacancy_info_from_api["experience"],
                        education=vacancy_info_from_api["education"],
                        place_of_work=vacancy_info_from_api["place_of_work"],
                        valid_until=vacancy_info_from_api["valid_until"],
                        original_link=vacancy_info_from_api["link"]
                    )
                    print(reverse('vacancies:search_vacancies', query=url_params))
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
                'vacancy_name': urllib.parse.quote_plus(self.request.GET.get('q')),
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