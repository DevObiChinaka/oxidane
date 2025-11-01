from django.urls import path
from . import views
from . import admin_views
from . import email_admin_views
from . import password_reset_views
from .jwt_auth import CustomTokenObtainPairView
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Simple health check endpoint"""
    return Response({'status': 'ok', 'message': 'API is running'})

urlpatterns = [
    # Health check
    path('health/', health_check, name='health_check'),
    
    # JWT Authentication (Standard)
    path('auth/token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Password Reset & OTP (New Secure System)
    path('auth/password-reset/request/', password_reset_views.request_password_reset, name='request_password_reset'),
    path('auth/password-reset/verify/', password_reset_views.verify_reset_token, name='verify_reset_token'),
    path('auth/password-reset/confirm/', password_reset_views.reset_password, name='reset_password'),
    path('auth/password-reset-otp/request/', password_reset_views.request_password_reset_otp, name='request_password_reset_otp'),
    path('auth/password-reset-otp/verify/', password_reset_views.verify_password_reset_otp, name='verify_password_reset_otp'),
    path('auth/otp/request/', password_reset_views.request_login_otp, name='request_login_otp'),
    path('auth/otp/verify/', password_reset_views.verify_login_otp, name='verify_login_otp'),
    path('auth/change-password/', password_reset_views.change_password, name='change_password_secure'),
    
    # Regular user authentication
    path('auth/check-email/', views.check_email, name='check_email'),
    path('auth/register/', views.register, name='register'),
    path('auth/login/', views.login, name='login'),
    path('auth/login-with-otp/', views.login_with_otp_request, name='login_with_otp_request'),
    path('auth/verify-login-otp/', views.verify_login_otp, name='verify_login_otp'),
    path('auth/resend-login-otp/', views.resend_login_otp, name='resend_login_otp'),
    path('auth/oauth/', views.oauth_callback, name='oauth_callback'),
    path('auth/profile/', views.user_profile, name='user_profile'),
    path('auth/update-profile/', views.update_profile, name='update_profile'),
    path('auth/change-password/', views.change_password, name='change_password'),
    path('auth/update-notifications/', views.update_notifications, name='update_notifications'),
    path('auth/get-notifications/', views.get_notifications, name='get_notifications'),
    path('auth/verify-email/', views.verify_email, name='verify_email'),
    path('auth/verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),
    path('auth/resend-verification-otp/', views.resend_verification_otp, name='resend_verification_otp'),
    path('auth/forgot-password/', views.forgot_password, name='forgot_password'),
    path('auth/reset-password/', views.reset_password, name='reset_password'),
    path('auth/resend-verification/', views.resend_verification, name='resend_verification'),
    path('auth/google/', views.google_oauth_init, name='google_oauth_init'),
    path('auth/google/callback/', views.google_oauth_callback, name='google_oauth_callback'),
    
    # Admin user management
    path('admin/users/', admin_views.user_list, name='admin_user_list'),
    path('admin/users/<uuid:user_id>/', admin_views.user_detail, name='admin_user_detail'),
    path('admin/users/<uuid:user_id>/action/', admin_views.user_action, name='admin_user_action'),
    path('admin/users-analytics/', admin_views.users_analytics, name='admin_users_analytics'),
    
    # Email template management
    path('admin/email-templates/', email_admin_views.email_templates_list, name='admin_email_templates'),
    path('admin/email-templates/<uuid:template_id>/', email_admin_views.email_template_detail, name='admin_email_template_detail'),
    path('admin/email-templates/<uuid:template_id>/preview/', email_admin_views.preview_email_template, name='admin_email_template_preview'),
    path('admin/email-templates/<uuid:template_id>/test/', email_admin_views.send_test_email, name='admin_send_test_email'),
    path('admin/email-templates/<uuid:template_id>/send/', email_admin_views.send_bulk_email, name='admin_send_bulk_email'),
    path('admin/email-template-types/', email_admin_views.email_template_types, name='admin_email_template_types'),
    path('admin/email-analytics/', email_admin_views.email_analytics, name='admin_email_analytics'),
]