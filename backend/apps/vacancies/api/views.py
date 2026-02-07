from django.shortcuts import get_object_or_404
from django.db.models.expressions import RawSQL

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.models import Applicant
from apps.accounts.api.permissions import IsInternalBot
from ..api_utils import get_vacancies_from_combined_api_sources, get_hh_vacancy_data_from_api, get_superjob_vacancy_data_from_api
from ..helpers import create_vacancy_instance
from ..models import Vacancy, SearchHistory, INITIAL_SOURCES
from ..recommendations.base import get_recommended_vacancies_by_content
from .serializers import VacancySerializer, WorkFormatsSerializer

class VacanciesViewset(ModelViewSet):
    model = Vacancy
    serializer_class = VacancySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.model.objects.filter(user=self.request.user)
    
    @action(methods=['get'], url_path="favourites", url_name="favourites", detail=False)
    def favourites(self, request, *args, **kwargs):
        '''Список ИЗБРАННЫХ вакансий пользователя'''
        serializer = self.get_serializer(self.get_queryset().filter(is_archived=False), many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        fav_vacancy = get_object_or_404(self.model, pk=pk)
        if fav_vacancy.user != request.user:
            return Response({"detail": "Только пользователь, добавивший вакансию в избранное, имеет к ней доступ."}, status=status.HTTP_403_FORBIDDEN)
        serializer = self.get_serializer(fav_vacancy)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(methods=['get'], url_path="recommendations", url_name="recommendations", detail=False)
    def recommendations(self, request, *args, **kwargs):
        recommendations_data = get_recommended_vacancies_by_content(user=request.user)
        return Response(recommendations_data, status=status.HTTP_200_OK)

    @action(methods=['post'], url_path='search', url_name='search', detail=False)
    def search(self, request, *args, **kwargs):
        query = request.data.get('query', '').lower()
        payment_from = request.data.get('payment_from', '')
        payment_from = int(payment_from) if payment_from else 0
        if query:
            city_ru_format = Applicant.objects.get(username=request.user.username).get_city_display()
            founded_vacancies_by_q = get_vacancies_from_combined_api_sources(city_ru_format, query, payment_from) # найденные вакансии, исходя из города соискателя и его запросов
            if not SearchHistory.objects.filter(user=request.user).annotate(is_match=RawSQL("search_query ILIKE '%%' || %s || '%%'", [query])).filter(is_match=True).exists() and len(founded_vacancies_by_q) > 0:
                SearchHistory.objects.create(user=request.user, search_query=query, results=len(founded_vacancies_by_q)) # создаёт Модель SearchHistory
            return Response({"vacancies": founded_vacancies_by_q, "results_amount": len(founded_vacancies_by_q)}, status=status.HTTP_200_OK)
        return Response({"detail": "Неправильный запрос."}, status=status.HTTP_400_BAD_REQUEST)

    @action(methods=['post'], url_path='add-to-favourites', url_name="add_to_favourites", detail=False)
    def add_to_favourites(self, request, *args, **kwargs):
        external_id = request.data.get('external_id')
        source = request.data.get('source') # source - SuperJob/HH
        if source in list([i[0] for i in INITIAL_SOURCES]):
            if self.model.objects.filter(external_id=external_id).exists():
                return Response({"detail": "Эта вакансия уже добавлена в избранное."}, status=status.HTTP_400_BAD_REQUEST)
            
            if source == INITIAL_SOURCES[0][0]:
                vacancy_info = get_superjob_vacancy_data_from_api(external_id)
            elif source == INITIAL_SOURCES[1][0]:
                vacancy_info = get_hh_vacancy_data_from_api(external_id)

            if vacancy_info:
                if self.model.objects.filter(user=request.user).count() < 5: # Ограничение на добавление вакансий в избранное - 5 штук
                    fav_vacancy_instance = create_vacancy_instance(request.user, vacancy_info)
                    serializer = self.get_serializer(fav_vacancy_instance)
                else:
                    applicant = Applicant.objects.get(username=request.user.username)
                    if applicant.is_sub:
                        fav_vacancy_instance = create_vacancy_instance(request.user, vacancy_info)
                        serializer = self.get_serializer(fav_vacancy_instance)
                    else:
                        return Response({"detail": "Ограничение на добавление вакансий в избранное. Станьте сабом, чтобы иметь больше возможностей!"}, status=status.HTTP_403_FORBIDDEN)
                return Response({"data": serializer.data, "message": "Вы успешно добавили вакансию в избранное."}, status=status.HTTP_201_CREATED)
            return Response({"detail": "Неправильный параметр - external_id."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"detail": "Неправильный параметр - source."}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['delete'], url_path="remove-from-favourites", url_name="remove_from_favourites", detail=True)
    def remove_from_favourites(self, request, pk=None):
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        title = obj.title
        obj.delete()
        return Response({"message": f"Успешное удаление вакансии: `{title}` из избранного."}, status=status.HTTP_200_OK)
    
    @action(methods=['get'], url_path="work-formats-names", url_name="get_favourite_vacancy_work_formats_names", detail=True)
    def get_favourite_vacancy_work_formats_names(self, request, pk=None):
        fav_vacancy = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = WorkFormatsSerializer(fav_vacancy.work_formats, many=True)
        work_formats = [i.get('name') for i in serializer.data]
        return Response(work_formats, status=status.HTTP_200_OK)