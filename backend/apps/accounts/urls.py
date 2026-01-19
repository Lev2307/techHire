from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import (
    LoginView, 
    sign_up_view, 
    telegram_auth, 
    PendingTechnologyListView,
    ProfileView, 
    AddOwnTechnologyToApplicantView, 
    EditProfileView, 
    EditOwnTechnologyFromApplicantView,
    delete_own_technology_from_applicant_view,
)

urlpatterns = [
    path('sign-up', sign_up_view, name='sign-up'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    path('telegram-auth/', telegram_auth, name='telegram-auth'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name="edit-profile"),
    path('profile/add-own-technology/', AddOwnTechnologyToApplicantView.as_view(), name="add-own-technology"),
    path('profile/edit-own-technology/<uuid:pk>/', EditOwnTechnologyFromApplicantView.as_view(), name="edit-own-technology"),
    path("profile/delete-own-technology/<uuid:pk>/", delete_own_technology_from_applicant_view, name="delete-own-technology"),
    path('admin/pending_technologies/', PendingTechnologyListView.as_view(), name="pending_technologies"),
]