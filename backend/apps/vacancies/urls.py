from django.urls import path

from .views import RecommendedVacanciesView, SearchVacanciesView, AddVacancyToFavourites

urlpatterns = [
    path('', RecommendedVacanciesView.as_view(), name='recom_vacancies'),
    path('search/', SearchVacanciesView.as_view(), name='search_vacancies'),
    path('add_to_favourites/<int:pk>/', AddVacancyToFavourites.as_view(), name='add_vacancy_to_favourites')
]