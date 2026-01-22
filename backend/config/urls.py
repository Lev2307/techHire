"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from rest_framework import routers

from apps.accounts.api.views import ApplicantsViewSet
from apps.vacancies.views import HomeView

router = routers.DefaultRouter(trailing_slash=False)
router.register(r'accounts', ApplicantsViewSet, basename="accounts")

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', HomeView.as_view(), name='homepage'),
    path('accounts/', include(('apps.accounts.urls', 'accounts'), namespace='accounts')),
    path('vacancies/', include(('apps.vacancies.urls', 'vacancies'), namespace='vacancies')),
    path('api/', include((router.urls, 'api'), namespace='api'))
]
