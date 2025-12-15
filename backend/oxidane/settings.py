
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Email configuration - Real SMTP (Gmail SSL)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', '465'))  # SSL port (working)
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'True') == 'True'
EMAIL_TIMEOUT = 30
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', 'oxiworldforexacademy@gmail.com')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', 'alhe mqzv yjra hqej')
DEFAULT_FROM_EMAIL = f'OxiWorld Forex Academy <{EMAIL_HOST_USER}>'

# Backup: Console output for debugging
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Alternative: File-based email for development
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'

# Build paths like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-tf%ns9(k(%&8@b69zyb^@9si24^m%mh$cp%l)$yfw&y3u4vpbl')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')



# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',  # AWS S3 storage backend
    'corsheaders',
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',  # For token rotation/blacklisting
    'oxidane',  # Core utilities (encryption, etc.)
    'users',
    'courses',
    'subscriptions',
    'settings_app',
]

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'VERIFYING_KEY': None,
    
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'subscriptions.middleware.SubscriptionValidationMiddleware',  # Real-time subscription validation
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'oxidane.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'oxidane.wsgi.application'



# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

# PostgreSQL Configuration (with SQLite fallback for local dev)
import dj_database_url

DATABASE_URL = os.getenv('DATABASE_URL', '')

# Temporarily comment out to backup SQLite data
USE_POSTGRESQL = DATABASE_URL and DATABASE_URL.startswith('postgresql')

if USE_POSTGRESQL:
    # Use PostgreSQL from environment variable
    DATABASES = {
        'default': dj_database_url.config(
            default=DATABASE_URL,
            conn_max_age=600,
            conn_health_checks=True,
        )
    }
else:
    # Fallback to SQLite for development
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

# File upload settings (increased for video uploads)
FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB for videos
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500MB for videos

# AWS S3 Configuration (Production)
USE_S3 = os.getenv('USE_S3', 'False') == 'True'

if USE_S3:
    # AWS Credentials
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'us-east-1')
    
    # S3 Settings
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_DEFAULT_ACL = None  # Use bucket ACL by default
    AWS_S3_OBJECT_PARAMETERS = {
        'CacheControl': 'max-age=86400',  # Cache for 1 day
    }
    AWS_S3_FILE_OVERWRITE = False
    AWS_QUERYSTRING_AUTH = True  # Generate signed URLs for private files
    AWS_S3_SIGNATURE_VERSION = 's3v4'
    
    # CloudFront CDN (optional but recommended)
    AWS_CLOUDFRONT_DOMAIN = os.getenv('AWS_CLOUDFRONT_DOMAIN', '')
    if AWS_CLOUDFRONT_DOMAIN:
        AWS_S3_CUSTOM_DOMAIN = AWS_CLOUDFRONT_DOMAIN
    
    # Static files (CSS, JS, Admin) - Public
    STATICFILES_STORAGE = 'oxidane.storage_backends.StaticStorage'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'
    
    # Media files (User uploads) - Private
    DEFAULT_FILE_STORAGE = 'oxidane.storage_backends.MediaStorage'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'
else:
    # Local storage (Development only)
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Custom Authentication Backend to support both email and username
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',  # Fallback
]

# CORS settings for frontend communication
CORS_ALLOWED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000,https://oxiworldforexacademy.com,https://www.oxiworldforexacademy.com'
    ).split(',')
]

CORS_ALLOW_CREDENTIALS = True

# CSRF trusted origins for cross-domain requests
CSRF_TRUSTED_ORIGINS = [
    origin.strip() for origin in os.getenv(
        'CSRF_TRUSTED_ORIGINS',
        'https://oxiworldforexacademy.com,https://www.oxiworldforexacademy.com'
    ).split(',')
]

# Allow specific headers for OAuth
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Frontend URL for email links
FRONTEND_URL = os.getenv('FRONTEND_URL', 'https://oxiworldforexacademy.com')

# Email configuration for real email sending (LEGACY - TLS version)
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'smtp.gmail.com'  # Gmail SMTP server
# EMAIL_PORT = 587
# EMAIL_USE_TLS = True
# EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')  # Your Gmail address
# EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')  # Your Gmail app password
# DEFAULT_FROM_EMAIL = f'OxiWorld Forex Academy <{EMAIL_HOST_USER}>' if EMAIL_HOST_USER else 'OxiWorld Forex Academy <noreply@oxiworld.com>'

# For development with file saving (backup option):
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
# EMAIL_FILE_PATH = BASE_DIR / 'sent_emails'

# For console output (development):
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Google OAuth Configuration
GOOGLE_OAUTH_CLIENT_ID = os.getenv('GOOGLE_OAUTH_CLIENT_ID', '')
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv('GOOGLE_OAUTH_CLIENT_SECRET', '')
GOOGLE_OAUTH_REDIRECT_URI = os.getenv('GOOGLE_OAUTH_REDIRECT_URI', 'http://localhost:8000/api/auth/google/callback/')


# ========================================
# TELEGRAM BOT CONFIGURATION
# ========================================
# Read from environment variables (will be moved to database in Phase 0.5)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '8386662254:AAFwqfss8wXc6SULYyX73yVvJ6OV686JI1I')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME', 'oxiworld_bot')
TELEGRAM_ADMIN_USER_ID = os.getenv('TELEGRAM_ADMIN_USER_ID', '1741840281')

# Telegram Groups Configuration (fallback, will be moved to database)
TELEGRAM_GROUPS = {
    'premium_signals': {
        'name': 'OxiWorld Premium Signals', 
        'chat_id': '-1002920074390',
        'type': 'group',
        'access_level': 'premium'
    },
    'education_group': {
        'name': 'OxiWorld Forex Mentorship',
        'chat_id': '-4885168917', 
        'type': 'group',
        'access_level': 'basic'
    },
    'vip_community': {
        'name': 'OxiWorld VIP Members',
        'chat_id': '-4811814960',
        'type': 'group', 
        'access_level': 'vip'
    },
}

# ========================================
# REDIS & CELERY CONFIGURATION
# ========================================
# Redis URL from environment
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)

# SSL Configuration for Redis Cloud (production only)
# Only apply SSL settings if using rediss:// scheme
if REDIS_URL.startswith('rediss://'):
    CELERY_BROKER_USE_SSL = {
        'ssl_cert_reqs': 'CERT_NONE'  # Accept self-signed certs from Redis Cloud
    }
    CELERY_REDIS_BACKEND_USE_SSL = {
        'ssl_cert_reqs': 'CERT_NONE'
    }

# Connection Settings (Optimized for Redis Free Tier - 30 max connections)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
CELERY_BROKER_POOL_LIMIT = 1  # Only 1 connection per worker to broker
CELERY_REDIS_MAX_CONNECTIONS = 3  # Max 3 connections total per worker

# Connection recycling - close connections after each task
CELERY_BROKER_TRANSPORT_OPTIONS = {
    'max_connections': 3,  # Limit pool size
    'socket_keepalive': True,
    'socket_keepalive_options': {
        1: 1,  # TCP_KEEPIDLE
        2: 2,  # TCP_KEEPINTVL
        3: 2,  # TCP_KEEPCNT
    },
}

# Result backend connection pooling
CELERY_REDIS_BACKEND_HEALTH_CHECK_INTERVAL = 30  # Check connection health every 30s
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {
    'max_connections': 3,
    'socket_keepalive': True,
}

# Task Serialization
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'

# Task Execution Settings
CELERY_TIMEZONE = 'UTC'
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes hard limit
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes soft limit
CELERY_TASK_ACKS_LATE = True  # Acknowledge tasks after completion (safer)
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Fetch one task at a time
CELERY_WORKER_MAX_TASKS_PER_CHILD = 20  # Recycle worker after 20 tasks (releases ALL connections)
CELERY_WORKER_DISABLE_RATE_LIMITS = True  # Disable rate limiting overhead

# Result Backend Settings
CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
CELERY_RESULT_PERSISTENT = False  # Don't persist results after expiry

# Celery Beat Schedule
# Don't define CELERY_BEAT_SCHEDULE here - it's configured in oxidane/celery.py
# If you define it here, it will override the schedule in celery.py

# ========================================
# CACHE CONFIGURATION
# ========================================
# Use Redis for caching with fallback to dummy cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 3,  # Further reduced to 3 for free tier
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 3,
            },
            'IGNORE_EXCEPTIONS': False,  # Show Redis errors to debug
        },
        'KEY_PREFIX': 'oxidane',
        'TIMEOUT': 300,  # 5 minutes default
    }
}

# ========================================
# ENCRYPTION CONFIGURATION
# ========================================
# Fernet encryption key for sensitive data (tokens, API keys, passwords)
# MUST be loaded from environment variable - see below for validation
ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY')  # Set in .env file

# ========================================
# MONITORING & LOGGING
# ========================================
# Sentry DSN for error tracking (optional, will be configured in Phase 9)
SENTRY_DSN = os.getenv('SENTRY_DSN', '')

# Structured logging with structlog (will be configured in Phase 1)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ============================================================================
# ENCRYPTION CONFIGURATION (Phase 0.5.12)
# ============================================================================
# Key for encrypting sensitive data (API keys, tokens, passwords)
# MUST be loaded from environment variable for security
# Generate a new key with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
# ============================================================================
if not os.getenv('ENCRYPTION_KEY'):
    raise ImproperlyConfigured(
        "ENCRYPTION_KEY environment variable is required. "
        "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

# ============================================================================
# CELERY EAGER MODE FOR DEVELOPMENT
# ============================================================================
# When Celery worker is not running, make tasks execute synchronously
# Set USE_CELERY_EAGER=True in .env for development without Celery
# IMPORTANT: Set to False in production with proper Celery workers
# ============================================================================
if os.getenv('USE_CELERY_EAGER', 'False').lower() == 'true':
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
    print("\n" + "="*70)
    print("⚠️  CELERY EAGER MODE ENABLED")
    print("   Tasks will run synchronously (blocking)")
    print("   Good for: Development, Testing")
    print("   Bad for: Production (blocks requests)")
    print("   To disable: Remove USE_CELERY_EAGER from .env")
    print("="*70 + "\n")