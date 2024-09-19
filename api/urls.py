from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.UserCreateAPIView.as_view(), name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('profile/', views.UserProfileAPIView.as_view(), name='profile'),
    path('otp_verification/<int:user_id>/', views.otp_verification, name='otp_verification'),
    path('password-reset/', views.password_reset_request, name='password_reset_request'),
    path('password-reset-confirm/', views.password_reset_confirm, name='password_reset_confirm'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/', views.RegisteredUsersView.as_view(), name='registered_users'), 
    
]
