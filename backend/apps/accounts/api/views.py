import time

import hmac
import hashlib

from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework import viewsets
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from config import settings
from apps.vacancies.api.serializers import WorkFormatsSerializer
from apps.vacancies.models import WORK_FORMAT_CHOICES, WorkFormat
from .serializers import ApplicantSerializer, ApplicantFullSerializer, TechnologySerializer, ApplicantLinkedTelegramSerializer, SpecializationSerializer
from .permissions import IsInternalBot
from ..models import Applicant, ApplicantLinkedTelegram, Technology, Specialization, CITY_CHOICES, EXPERIENCE_CHOICES
from ..tasks import send_telegram_message

class ApplicantsViewSet(viewsets.ModelViewSet):
    queryset = Applicant.objects.prefetch_related('technologies').all()
    serializer_class = ApplicantSerializer

    def get_permissions(self):
        if self.action in ['create', 'telegram_auth']: # аутентификация
            permission_classes = []
        elif self.action in ['list', 'retrieve', 'pending_technologies_list', 'moderate_technology']: # permissions доступные только админам
            permission_classes = [IsAdminUser]
        elif self.action in ['linked_telegram_info', 'retrieve_specialization', 'retrieve_technology']: # permissions для доступа боту
            permission_classes = [IsInternalBot]
        elif self.action in ['applicant_created_technologies_list']: # permission для авторизованных пользователей или для бота
            permission_classes = [IsAuthenticated | IsInternalBot]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None):
        applicant = get_object_or_404(self.queryset, pk=pk)
        serializer = self.get_serializer(applicant)
        return Response(serializer.data)
    
    def perform_create(self, serializer):
        instance = serializer.save()
        token = Token.objects.create(user=instance)
        return token

    def create(self, request, *args, **kwargs):
        user_data = request.data.get('tg_user_data')
        if not user_data:
            return Response({"detail": "Данные телеграм не найдены в сессии."}, status=status.HTTP_400_BAD_REQUEST)
        
        if time.time() - int(user_data.get('auth_date', 0)) > 300:
            return Response({"detail": "Время сессии истекло."}, status=status.HTTP_400_BAD_REQUEST)

        if user_data.get('hash') != user_data.get('secret'):
            return Response({"detail": "Ошибка безопасности: хеш не совпал."}, status=status.HTTP_400_BAD_REQUEST) 
        
        serializer = self.get_serializer(
            data=request.data,
            context={'tg_user_data': user_data}
        )
        serializer.is_valid(raise_exception=True)
        token = self.perform_create(serializer)

        telega = get_object_or_404(ApplicantLinkedTelegram, user_id=user_data.get('id')) # сохраняю токен в модель привязанного соискателем телеграма 
        telega.auth_token = token.key
        telega.save()

        return Response({
            'message': 'Вы успешно вошли в систему.', 
            "token": token.key,
            "username": serializer.data["username"]
        }, status=status.HTTP_201_CREATED)
    
    @action(methods=["get"], url_path="telegram-auth", url_name="telegram_auth", detail=False)
    def telegram_auth(self, request, *args, **kwargs):
        data = request.query_params
        if time.time() - int(data.get('auth_date', 0)) > 300:
            return Response({"detail": "Время сессии истекло"}, status=status.HTTP_401_UNAUTHORIZED)

        hash = data.get('hash')
        secret_key = hashlib.sha256(settings.TELEGRAM_BOT_TOKEN.encode()).digest()
        check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash'])
        secret = hmac.new(secret_key, check_string.encode(), hashlib.sha256).hexdigest()
        if secret != hash:
            return Response({"detail": "Ошибка безопасности: хеш не совпал"}, status=status.HTTP_400_BAD_REQUEST)
        
        user_data = {
            'id': data.get('id'),
            'username': data.get('username'),
            'first_name': data.get('first_name'),
            'auth_date': data.get('auth_date'),
            'secret': secret,
            'hash': hash
        }
        telega = ApplicantLinkedTelegram.objects.filter(user_id=user_data["id"]).first()
        if telega:
            user = get_object_or_404(Applicant, linked_telegram=telega)
            token, created = Token.objects.get_or_create(user=user)

            if created: # если токен создался заново, то перезаписываю его в бд
                telega.auth_token = token.key
                telega.save()
            return Response({
                "message": "Успешный вход в систему.", 
                "token": token.key,
                "username": user.username,
            }, 
            status=status.HTTP_200_OK)
        
        return Response({
            "status": "register",
            "message": "Аккаунт не найден, пожалуйста, завершите регистрацию.",
            "tg_user_data": user_data,
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path="logout", url_name='logout')
    def logout(self, request, *args, **kwargs):
        request.user.auth_token.delete() # Удаляем токен из бд
        return Response({"message": "Успешный выход из системы"})

    @action(detail=False, methods=['get', 'patch', 'put'], url_path='me', url_name='me')
    def me(self, request):
        applicant = request.user
        
        if request.method == 'GET':
            serializer = self.get_serializer(applicant) 
            return Response(serializer.data)
        
        serializer = self.get_serializer(applicant, data=request.data, partial=True, user=applicant)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
        
    @action(methods=['post'], url_path='add-technology', url_name='add_technology', detail=False)
    def add_own_technology(self, request, *args, **kwargs):
        applicant = request.user
        serializer = TechnologySerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            instance = serializer.save(creator=applicant)
            applicant.technologies.add(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["put", "patch"], url_path='edit-technology/(?P<tech_id>[^/.]+)', url_name='edit_technology', detail=True)
    def edit_own_technology(self, request, pk=None, tech_id=None): # pk - для Пользователя, tech_id - для id технологии
        technology = get_object_or_404(Technology, pk=tech_id)
        applicant = request.user
        if technology.creator != applicant:
            return Response({"detail": "Доступ к технологии может получить только её владелец."}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = TechnologySerializer(technology, data=request.data, partial=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.data, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=["delete"], url_path='delete-technology/(?P<tech_id>[^/.]+)', url_name='delete_technology', detail=True)
    def delete_own_technology(self, request, pk=None, tech_id=None):
        tech = get_object_or_404(Technology, pk=tech_id)
        applicant = request.user
        if tech.creator != applicant:
            return Response({"detail": "Доступ к технологии может получить только её владелец."}, status=status.HTTP_403_FORBIDDEN)

        if tech.is_approved:
            return Response({"detail": "Нельзя удалить одобренную технологию из общей базы."}, status=status.HTTP_400_BAD_REQUEST)
        
        tech.delete()
        return Response({"message": "Технология была успешна удалена!"}, status=status.HTTP_204_NO_CONTENT)
    
    @action(methods=["get"], url_path="applicant-technologies", url_name="applicant_created_technologies_list", detail=True)
    def applicant_created_technologies_list(self, request, *args, **kwargs):
        applicant_created_techs_list = Technology.objects.filter(creator=request.user).order_by("-created_at")
        serializer = TechnologySerializer(applicant_created_techs_list, many=True)
        return Response(serializer.data)
    
    @action(methods=["get"], url_path="pending-technologies", url_name="pending_technologies_list", detail=False)
    def pending_technologies_list(self, request, *args, **kwargs):
        techs_list_non_approved = Technology.objects.filter(is_approved=False).order_by("-created_at")
        serializer = TechnologySerializer(techs_list_non_approved, many=True)
        return Response(serializer.data)
    
    @action(methods=["patch", "delete"], url_path="moderate-technology/(?P<tech_id>[^/.]+)", url_name="moderate_technology", detail=False)
    def moderate_technology(self, request, tech_id=None):
        tech = get_object_or_404(Technology, pk=tech_id)
        name, creator = tech.name, tech.creator
        if tech.is_approved:
            return Response({"detail": "Технология уже прошла модерацию."}, status=status.HTTP_403_FORBIDDEN)
        
        if request.method == "DELETE":
            tech.delete()
            if creator.notifications_enabled:
                if creator.linked_telegram and creator.linked_telegram.is_active: # проверка если логинился через тг и привязан ли тг к боту
                    send_telegram_message.delay(f"Ваш вариант технологии - {name} был отклонен модерацией ⛔", creator.id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        
        tech.is_approved = True
        tech.save()
        if creator.notifications_enabled:
            if creator.linked_telegram and creator.linked_telegram.is_active:
                send_telegram_message.delay(f"Ваш вариант технологии - {name} был подтвержден модерацией ✅", creator.id)
        return Response({"message": f"Технология {tech.name} была подтверждена модерацией"}, status=status.HTTP_200_OK)
    
    @action(methods=['get'], url_path='by-telegram', url_name="by_telegram", detail=False)
    def by_telegram(self, request, *args, **kwargs):
        serializer = ApplicantFullSerializer(request.user)
        return Response(serializer.data)
    
    @action(methods=['get', 'patch'], url_path='linked-telegram-info/(?P<tg_id>[^/.]+)', url_name="linked_telegram_info", detail=False)
    def linked_telegram_info(self, request, tg_id=None):
        linked_telegram = get_object_or_404(ApplicantLinkedTelegram, user_id=tg_id)
        if request.method == "GET":
            serializer = ApplicantLinkedTelegramSerializer(linked_telegram)
            return Response(serializer.data)
        
        linked_telegram.auth_token = "" # делаю токен пустым, поскольку появилась ошибка 401 при попытке сделать запрос, когда токен (drf) был удалён из базы
        linked_telegram.save()

    @action(methods=['get'], url_path="all-available-cities-info", url_name="all_available_cities_info", detail=False)
    def all_available_cities_info(self, request, *args, **kwargs):
        applicant = request.user
        cities = {}
        for city in CITY_CHOICES:
            if not cities.get(city[0]):
                if city[0] == applicant.city:
                    cities[city[0]] = (city[1], 'selected')
                else:
                    cities[city[0]] = (city[1], 'not_selected')
        return Response(cities)
        
    @action(methods=['get'], url_path='all-available-experience-info', url_name='all_available_experience_info', detail=False)
    def all_available_experience_info(self, request, *args, **kwargs):
        applicant = request.user
        experiences = {}
        for exp in EXPERIENCE_CHOICES[1:]:
            if not experiences.get(exp[0]):
                if applicant.experience == exp[0]:
                    experiences[exp[0]] = (exp[1], 'selected')
                else:
                    experiences[exp[0]] = (exp[1], 'not_selected')
        return Response(experiences)
    
    @action(methods=['get'], url_path="all-available-work-formats-info", url_name="all_available_work_formats_info", detail=False)
    def all_available_work_formats_info(self, request, *args, **kwargs):
        applicant_work_formats = [wf.name for wf in request.user.preferred_work_formats.all()]
        work_formats = {}
        for work_format in WORK_FORMAT_CHOICES[1:]:
            if not work_formats.get(work_format[0]):
                if work_format[1] in applicant_work_formats:
                    work_formats[work_format[0]] = (WorkFormat.objects.get(name_eng=work_format[0]).id, work_format[1], 'selected')
                else:
                    work_formats[work_format[0]] = (WorkFormat.objects.get(name_eng=work_format[0]).id, work_format[1], 'not_selected')
        return Response(work_formats)

    @action(methods=['get'], url_path="list-applicant-work-formats-ids", url_name="list_applicant_work_formats_ids", detail=False)
    def list_applicant_work_formats_ids(self, request, *args, **kwargs):
        work_formats = request.user.preferred_work_formats.all()
        serializer = WorkFormatsSerializer(work_formats, many=True)
        data = [str(i.get('id')) for i in serializer.data]
        return Response(data)

    @action(methods=['get'], url_path="all-available-specializations-info", url_name="all_available_specializations_info", detail=False)
    def all_available_specializations_info(self, request, *args, **kwargs):
        specializations = Specialization.objects.all()
        results = [
            {
                "id": spec.id,
                "name": spec.name,
                "status": "selected" if spec in request.user.specializations.all() else "not_selected"
            }
            for spec in specializations
        ]
        return Response(results)
    
    @action(methods=['get'], url_path="list-applicant-specializations-ids", url_name="list_applicant_specializations_ids", detail=False)
    def list_applicant_specializations_ids(self, request, *args, **kwargs):
        applicant_specializations = request.user.specializations.all()
        serializer = SpecializationSerializer(applicant_specializations, many=True)
        specializations_list = [str(i.get('id')) for i in serializer.data]
        return Response(specializations_list)
    
    @action(methods=['get'], url_path="technologies-list-by-query", url_name="technologies_list_by_query", detail=False)
    def technologies_list_by_query(self, request, *args, **kwargs):
        applicant = request.user
        query = request.query_params.get('query', '')
        if query:
            technologies = Technology.objects.filter(Q(is_approved=True) | Q(creator=applicant)).filter(name__icontains=query)
            results = [
                {
                    "id": tech.id,
                    "name": tech.name,
                    "status": "selected" if tech in applicant.technologies.all() else "not_selected"
                }
                for tech in technologies
            ]
            return Response(results)
        return Response({"detail": "Нет параметра поиска - query"}, status=status.HTTP_400_BAD_REQUEST)
    
    @action(methods=['get'], url_path="specializations/(?P<spec_id>[^/.]+)", url_name="retrieve_specialization", detail=False)
    def retrieve_specialization(self, request, spec_id=None):
        specialization = get_object_or_404(Specialization, pk=spec_id)
        serializer = SpecializationSerializer(specialization)
        return Response(serializer.data)
    
    @action(methods=['get'], url_path="technologies/(?P<tech_id>[^/.]+)", url_name="retrieve_technology", detail=False)
    def retrieve_technology(self, request, tech_id=None):
        technology = get_object_or_404(Technology, pk=tech_id)
        serializer = TechnologySerializer(technology)
        return Response(serializer.data)
    
    @action(methods=['get'], url_path="list-applicant-technologies-ids", url_name="list_applicant_technologies_ids", detail=False)
    def list_applicant_technologies_ids(self, request, *args, **kwargs):
        applicant_technologies = request.user.technologies.all()
        serializer = TechnologySerializer(applicant_technologies, many=True)
        technologies_list_ids = [str(i.get('id')) for i in serializer.data]
        return Response(technologies_list_ids)