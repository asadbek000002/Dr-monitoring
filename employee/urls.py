from django.urls import path
from .views import LoginView, LogoutView, UserProfileView

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('users/', UserProfileView.as_view(), name='user-list'),
]
