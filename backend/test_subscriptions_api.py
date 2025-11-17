"""Test the my-subscriptions API endpoint"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'oxidane.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from rest_framework.test import force_authenticate
from subscriptions.user_views import my_subscriptions

User = get_user_model()

# Get the user
user = User.objects.filter(email='obbinachidera123@gmail.com').first()

if not user:
    print("User not found!")
else:
    print(f"Testing API for user: {user.email}")
    
    # Create a fake request
    factory = RequestFactory()
    request = factory.get('/api/subscriptions/my-subscriptions/')
    force_authenticate(request, user=user)
    
    # Call the view
    response = my_subscriptions(request)
    
    print(f"\nAPI Response Status: {response.status_code}")
    print(f"\nAPI Response Data:")
    import json
    print(json.dumps(response.data, indent=2))
