"""
Django settings for moine_back project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
import sys
import getconf
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

IS_LOCAL_DEV = bool(os.environ.get("TELESCOOP_DEV"))
DEBUG = IS_LOCAL_DEV
IS_TESTING = "test" in sys.argv

if IS_LOCAL_DEV:
    config_paths = ["local_settings.conf"]
else:
    config_paths = [os.environ["CONFIG_PATH"]]
config = getconf.ConfigGetter("myproj", config_paths)

if IS_LOCAL_DEV:
    SECRET_KEY = "django-insecure-zdvs0+i17^0*8w0nd%0mtoa69)%#%cp37=8t2^2s0ung)zp(51"
    ALLOWED_HOSTS = ["*"]
else:
    SECRET_KEY = config.getstr("security.secret_key")
    ALLOWED_HOSTS = config.getlist("security.allowed_hosts")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "versatileimagefield",
    "hijack",
    "hijack.contrib.admin",
    "telescoop_auth",
    "main",
    "rest_framework",
    "telescoop_backup",
    "django_quill",
]
if IS_LOCAL_DEV:
    INSTALLED_APPS.append("debug_toolbar")
else:
    # this is necessary for text search
    INSTALLED_APPS.append("django.contrib.postgres")

if IS_LOCAL_DEV:
    INSTALLED_APPS.append("corsheaders")

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "rollbar.contrib.django.middleware.RollbarNotifierMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "hijack.middleware.HijackUserMiddleware",
]

ROOT_URLCONF = "moine_back.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "moine_back.wsgi.application"

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

if IS_LOCAL_DEV:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
    if not IS_TESTING and config.getstr("database.postgres"):
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": config.getstr("database.name"),
                "USER": config.getstr("database.user"),
                "PASSWORD": config.getstr("database.password"),
            }
        }
        # this is necessary for text search
        INSTALLED_APPS.append("django.contrib.postgres")
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config.getstr("database.name"),
            "USER": config.getstr("database.user"),
            "PASSWORD": config.getstr("database.password"),
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "fr-fr"

TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True

STATIC_URL = "static/"
MEDIA_URL = "media/"
if IS_LOCAL_DEV:
    STATIC_ROOT = BASE_DIR / "collected_static"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")
else:
    STATIC_ROOT = config.getstr("staticfiles.static_root")

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# production errors
if not IS_LOCAL_DEV:
    ROLLBAR = {
        "access_token": "c4ebf44512b4479fb018ee413ac08d2a",
        "environment": "development"
        if DEBUG
        else config.getstr("environment.environment", "production"),
        "root": BASE_DIR,
        "capture_email": True,
    }
    import rollbar

    rollbar.init(**ROLLBAR)

# CORS
if IS_LOCAL_DEV:
    CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
    CORS_ALLOW_CREDENTIALS = True
    CSRF_TRUSTED_ORIGINS = ["http://localhost:3000"]
else:
    # see https://docs.djangoproject.com/en/4.0/ref/settings/#secure-proxy-ssl-header
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")


# django-hijack
HIJACK_ALLOW_GET_REQUESTS = True

AUTH_USER_MODEL = "main.User"

# camel case for DRF
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": (
        "djangorestframework_camel_case.render.CamelCaseJSONRenderer",
        # "djangorestframework_camel_case.render.CamelCaseBrowsableAPIRenderer",
        # below renderer can be useful to debug queries with django-debug-toolbar
        "main.renderer.RendererNoForm",
    ),
    "DEFAULT_PARSER_CLASSES": (
        "djangorestframework_camel_case.parser.CamelCaseFormParser",
        "djangorestframework_camel_case.parser.CamelCaseMultiPartParser",
        "djangorestframework_camel_case.parser.CamelCaseJSONParser",
    ),
}

# File storage
if not IS_LOCAL_DEV:
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    AWS_S3_ACCESS_KEY_ID = config.getstr("external_file_storage.access")
    AWS_S3_SECRET_ACCESS_KEY = config.getstr("external_file_storage.secret")
    AWS_S3_ENDPOINT_URL = config.getstr("external_file_storage.endpoint_url")
    AWS_STORAGE_BUCKET_NAME = config.getstr("external_file_storage.bucket")
    AWS_S3_REGION_NAME = "paris"

# django debug toolbar
if IS_LOCAL_DEV:
    INTERNAL_IPS = ["127.0.0.1", "localhost"]

# mail
DEFAULT_FROM_EMAIL = "La Base <no-reply@telescoop.fr>"
if IS_LOCAL_DEV:
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    ANYMAIL = {
        "MAILGUN_API_KEY": config.getstr("mail.api_key"),
        "MAILGUN_SENDER_DOMAIN": "mail.telescoop.fr",
        "MAILGUN_API_URL": "https://api.eu.mailgun.net/v3",
    }
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    SERVER_EMAIL = "no-reply@telescoop.fr"

# domain
if IS_LOCAL_DEV:
    DOMAIN = "localhost:8000"
else:
    DOMAIN = ALLOWED_HOSTS[0]

# allow password reset for a week (by default 1 day)
PASSWORD_RESET_TIMEOUT = 3600 * 24 * 7

# telescoop-backup
BACKUP_ACCESS = config.getstr("db_backup.access")
BACKUP_SECRET = config.getstr("db_backup.secret")
BACKUP_BUCKET = config.getstr("db_backup.bucket")

# pagination
BASE_PAGE_SIZE = 12
RESOURCE_PAGE_SIZE = 12

VERSATILEIMAGEFIELD_RENDITION_KEY_SETS = {
    "base_profile": [
        ("full_size", "url"),
        ("option", "crop__30x30"),
        ("miniature", "crop__100x100"),
        ("index", "crop__144x144"),
    ],
    "base_cover": [
        ("full_size", "url"),
        ("miniature", "crop__382x116"),
        ("index", "crop__1200x250"),
    ],
    "resource_profile": [
        ("full_size", "url"),
        ("miniature", "crop__322x252"),
    ],
    "cropping_preview": [("medium", "to-width__100x100")],
    "": [("full_size", "url")],
}
