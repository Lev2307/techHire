from django.urls import path

from .views import RecommendedVacanciesView, SearchVacanciesView

urlpatterns = [
    path('', RecommendedVacanciesView.as_view(), name='recom_vacancies'),
    path('search/', SearchVacanciesView.as_view(), name='search_vacancies')
]