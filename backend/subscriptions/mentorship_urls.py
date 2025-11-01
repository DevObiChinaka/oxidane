# Mentorship URL Configuration
from django.urls import path
from . import mentorship_admin_views, mentorship_payments

urlpatterns = [
    # Mentorship Admin Views
    path('admin/mentorship/subscriptions/', 
         mentorship_admin_views.mentorship_subscription_list, 
         name='mentorship_subscriptions'),
    
    path('admin/mentorship/sessions/', 
         mentorship_admin_views.mentorship_session_management, 
         name='mentorship_sessions'),
    
    path('admin/mentorship/analytics/', 
         mentorship_admin_views.mentorship_analytics, 
         name='mentorship_analytics'),
    
    # Telegram tasks are handled by the existing telegram queue system
    
    path('admin/mentorship/extend/<str:subscription_id>/', 
         mentorship_admin_views.extend_subscription, 
         name='extend_mentorship'),
    
    # Payment Processing
    path('mentorship/payment/initialize/', 
         mentorship_payments.initiate_mentorship_payment, 
         name='initiate_mentorship_payment'),
    
    path('mentorship/payment/verify/', 
         mentorship_payments.verify_mentorship_payment, 
         name='verify_mentorship_payment'),
    
    path('mentorship/webhook/paystack/', 
         mentorship_payments.paystack_mentorship_webhook, 
         name='mentorship_paystack_webhook'),
    
    # Public API endpoints
    path('mentorship/plans/', 
         mentorship_payments.get_mentorship_plans, 
         name='mentorship_plans'),
    
    path('mentorship/user/status/', 
         mentorship_payments.get_user_mentorship_status, 
         name='user_mentorship_status'),
]