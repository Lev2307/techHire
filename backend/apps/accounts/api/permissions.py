from rest_framework import permissions
from django.conf import settings

class IsInternalBot(permissions.BasePermission):
    def has_permission(self, request, view):
        # Проверяем наличие секретного токена в заголовках
        auth_token = request.headers.get('X-Internal-Token')
        return auth_token == settings.TELEGRAM_BOT_TOKEN