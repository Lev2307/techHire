from django.shortcuts import render, HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.utils.decorators import method_decorator

from django.views import generic, View
from django.views.decorators.csrf import csrf_exempt


from .models import Vacancy

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

@method_decorator(csrf_exempt, name='get')
class RecommendedVacanciesView(View):
    template_name = 'vacancies.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

class SearchVacanciesView(View):
    template_name = 'search.html'
    
    def get(self, request, *args, **kwargs):
        print('search')
        return render(request, self.template_name)