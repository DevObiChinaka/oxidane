from django.urls import path
from . import admin_views, views

app_name = 'courses'

urlpatterns = [
    # Public course endpoints
    path('courses/', views.list_courses, name='list_courses'),
    path('courses/enrolled/', views.enrolled_courses, name='enrolled_courses'),
    path('courses/<slug:slug>/', views.course_detail, name='course_detail'),
    path('courses/<slug:slug>/enroll/', views.enroll_course, name='enroll_course'),
    path('courses/lessons/<uuid:lesson_id>/progress/', views.update_lesson_progress, name='update_lesson_progress'),
    
    # Admin dashboard endpoints
    path('admin/dashboard/metrics/', admin_views.admin_dashboard_metrics, name='admin_dashboard_metrics'),
    path('admin/dashboard/analytics/', admin_views.admin_course_analytics, name='admin_course_analytics'),
    
    # Course management
    path('admin/courses/', admin_views.admin_courses, name='admin_courses'),
    path('admin/courses/<uuid:course_id>/', admin_views.admin_course_detail, name='admin_course_detail'),
    path('admin/courses/<uuid:course_id>/publish/', admin_views.admin_course_publish, name='admin_course_publish'),
    path('admin/courses/<uuid:course_id>/analytics/', admin_views.admin_course_analytics, name='admin_course_analytics'),
    
    # Lesson management
    path('admin/lessons/', admin_views.admin_lessons_list, name='admin_lessons_list'),
    path('admin/courses/<uuid:course_id>/lessons/', admin_views.admin_course_lessons, name='admin_course_lessons'),
    path('admin/lessons/<uuid:lesson_id>/', admin_views.admin_lesson_detail, name='admin_lesson_detail'),
]