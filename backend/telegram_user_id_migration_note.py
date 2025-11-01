"""
Add Telegram user ID storage to the User model
Run: python manage.py makemigrations
Then: python manage.py migrate
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

# We'll add this field to the existing User model
# Add this to users/models.py in the User model:
# telegram_user_id = models.BigIntegerField(null=True, blank=True, unique=True, help_text="Telegram user ID for bot operations")