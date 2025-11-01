from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('django-admin/', admin.site.urls),  # Changed from 'admin/' to avoid conflict with Next.js frontend
    path('api/', include('users.urls')),
    path('api/', include('courses.urls')),
    path('api/', include('subscriptions.urls')),
    path('api/', include('subscriptions.mentorship_urls')),
    path('api/admin/', include('settings_app.urls')),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
