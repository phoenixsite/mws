"""
Django settings for mws project.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env_path = load_dotenv(os.path.join(BASE_DIR, "mws_settings.env"))
load_dotenv(env_path)

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG")

ALLOWED_HOSTS = ['127.0.0.1', 'mws.local', '.mws.local']


# Application definition

INSTALLED_APPS = [
    'tenants.apps.TenantsConfig',
    'mws.apps.MWSAdminConfig',
    'mws_main.apps.MwsMainConfig',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'tenants.middlewares.TenantMiddleware',
    'mws_main.middleware.StatsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'mws_main.middleware.UserTypeMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mws.urls'

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

WSGI_APPLICATION = 'mws.wsgi.application'

from django.db.backends.postgresql.psycopg_any import IsolationLevel

env_path = load_dotenv(os.path.join(BASE_DIR, "mws_db_settings.env"))
load_dotenv(env_path)

# The default database must not be empty. The application
# connects to it to create the tenants' databases. 
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get("MWS_DB_NAME"),
        'USER': os.environ.get("MWS_DB_USER"),
        'PORT': os.environ.get("MWS_DB_PORT"),
        'HOST': os.environ.get("MWS_DB_HOST"),
        'CONN_MAX_AGE': 120,
        'OPTIONS': {
            'client_encoding': 'UTF8',
            'isolation_level': IsolationLevel.SERIALIZABLE,
        },
    },
}

with open(os.environ.get("MWS_PASSWD_FILE")) as f:
    password = f.read().strip()
    DATABASES['default']['PASSWORD'] = password

DATABASE_ROUTERS = [
    'tenants.router.TenantSpecRouter',
    'tenants.router.GeneralMWSRouter',
]

# Password validation
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
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

INTERNAL_IPS = [
    "127.0.0.1",
]

MEDIA_ROOT = "media/"
MEDIA_URL = "/media/"
LOGIN_REDIRECT_URL = None
LOGIN_URL = "/store/login"

# Path to database settings dir
PATH_DB_SETTINGS = Path(BASE_DIR, "tenants/database_settings")

# Fetch dynamically the tenants databases information
import os

for fname in os.listdir(PATH_DB_SETTINGS):
    full_path = os.path.join(PATH_DB_SETTINGS, fname)

    with open(full_path, "r") as setting_file:
        content = setting_file.read()
        exec(content)

PERMISSIONS_FIXTURE = "permissions.json"
