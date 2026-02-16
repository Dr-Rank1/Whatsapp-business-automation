"""
Core app URL configuration for authentication and user management.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    RegisterView, LoginView, LogoutView, ChangePasswordView,
    UserProfileView, UserView, refresh_token_view, user_stats
)

urlpatterns = [
    # Authentication endpoints
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/refresh/custom/', refresh_token_view, name='token_refresh_custom'),
    
    # User management endpoints
    path('me/', UserProfileView.as_view(), name='user_profile'),
    path('user/', UserView.as_view(), name='user_detail'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),
    path('stats/', user_stats, name='user_stats'),
]
