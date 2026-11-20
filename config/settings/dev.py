from .base import *

ENVIRONMENT= "development"
DEBUG = True

CSRF_TRUSTED_ORIGINS = [
    "https://*.trycloudflare.com",
]

ALLOWED_HOSTS = ["*"]

# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}