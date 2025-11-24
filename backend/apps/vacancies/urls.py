from django.urls import path

from .views import RecommendedVacanciesView, SearchVacanciesView, FavouriteVacanciesList, AddVacancyToFavourites, RemoveVacancyFromFavorites

urlpatterns = [
    path('', RecommendedVacanciesView.as_view(), name='recom_vacancies'),
    path('search/', SearchVacanciesView.as_view(), name='search_vacancies'),
    path('favorites/', FavouriteVacanciesList.as_view(), name="favourite_vacancies"),
    path('add_to_favourites/<int:pk>/', AddVacancyToFavourites.as_view(), name='add_vacancy_to_favourites'),
    path('remove_vacancy_from_favourites/<int:pk>/', RemoveVacancyFromFavorites.as_view(), name='remove_vacancy_from_favourites')
]