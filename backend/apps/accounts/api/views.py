import time

import hmac
import hashlib

from django.shortcuts import get_object_or_404
from django.contrib.auth import login

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from config import settings
from .serializers import ApplicantSerializer, TechnologySerializer
from .permissions import IsInternalBot
from ..models import Applicant, ApplicantLinkedTelegram, Technology
from ..tasks import send_telegram_message

class ApplicantsViewSet(viewsets.ModelViewSet):
    queryset = Applicant.objects.prefetch_related('technologies').all()
    serializer_class = ApplicantSerializer

    def get_permissions(self):
        if self.action in ['create', 'telegram_auth']: # аутентификация
            permission_classes = []
        elif self.action in ['list', 'retrieve', 'pending_technologies_list', 'moderate_technology']: # permissions доступные только админам
            permission_classes = [IsAdminUser]
        elif self.action in ['by_telegram']: # permissions для доступа боту
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
        login(self.request, instance)
        del self.request.session['tg_user_data'] # удаление ключа с тгшной инфой из сессии

    def create(self, request, *args, **kwargs):
        user_data = self.request.session.get('tg_user_data')
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
        self.perform_create(serializer)

        return Response({'message': 'Вы успешно вошли в систему.', "user": serializer.data["username"]}, status=status.HTTP_201_CREATED)
    
    @action(methods=["GET"], url_path="telegram-auth", url_name="telegram_auth", detail=False)
    def telegram_auth(self, request, *args, **kwargs):
        data = request.GET
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
        request.session['tg_user_data'] = user_data
        telega = ApplicantLinkedTelegram.objects.filter(user_id=user_data["id"]).first()
        if telega:
            user = get_object_or_404(Applicant, linked_telegram=telega)
            login(request, user)
            del request.session['tg_user_data']
            return Response({"message": "Успешный вход в систему.", "user": user.username}, status=status.HTTP_200_OK)
        
        return Response({
            "status": "register",
            "message": "Аккаунт не найден, пожалуйста, завершите регистрацию.",
            "tg_user_data": user_data
        }, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get', 'patch', 'put'], url_path='me', url_name='me')
    def me(self, request):
        applicant = get_object_or_404(Applicant, username=request.user.username)
        
        if request.method == 'GET':
            serializer = self.get_serializer(applicant) 
            return Response(serializer.data)
        
        serializer = self.get_serializer(applicant, data=request.data, partial=True, user=request.user)
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
    
    @action(methods=['get'], url_path='by-telegram/(?P<tg_id>[^/.]+)', url_name="by_telegram", detail=False)
    def by_telegram(self, request, tg_id=None):
        applicant = get_object_or_404(Applicant, linked_telegram__user_id=tg_id)
        serializer = self.get_serializer(applicant)
        return Response(serializer.data)