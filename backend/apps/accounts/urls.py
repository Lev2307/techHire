from django.urls import path
from django.contrib.auth.views import LogoutView

from .views import ProfileView, LoginView, sign_up_view, telegram_auth, AddOwnTechnologyToApplicantView, EditProfileView, PendingTechnologyListView


urlpatterns = [
    path('sign-up', sign_up_view, name='sign-up'),
    path('login', LoginView.as_view(), name='login'),
    path('logout', LogoutView.as_view(next_page='/'), name='logout'),
    path('telegram-auth', telegram_auth, name='telegram-auth'),
    path('profile', ProfileView.as_view(), name='profile'),
    path('profile/add-own-technology', AddOwnTechnologyToApplicantView.as_view(), name="add-own-technology"),
    path('profile/edit', EditProfileView.as_view(), name="edit-profile"),
    path('admin/pending_technologies', PendingTechnologyListView.as_view(), name="pending_technologies")
]