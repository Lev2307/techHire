from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import RegisterApplicantView, LoginView, telegram_auth


urlpatterns = [
    path('signup', RegisterApplicantView.as_view(), name='sign-up'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(next_page='/'), name='logout'),
    path('telegram/auth', telegram_auth, name="telegram_auth"),
]