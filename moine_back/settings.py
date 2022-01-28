"""
Django settings for moine_back project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

import os
import getconf
from pathlib import Path

# local config
config = getconf.ConfigGetter(
    "myproj", ["local_settings.conf", "/etc/telescoop/moine/settings.ini"]
)

BASE_DIR = Path(__file__).resolve().parent.parent

IS_LOCAL_DEV = bool(os.environ.get("TELESCOOP_DEV"))
DEBUG = IS_LOCAL_DEV


if IS_LOCAL_DEV:
    SECRET_KEY = "django-insecure-zdvs0+i17^0*8w0nd%0mtoa69)%#%cp37=8t2^2s0ung)zp(51"
    ALLOWED_HOSTS = []
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
    "debug_toolbar",
    "hijack",
    "hijack.contrib.admin",
]

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
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

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


STATIC_URL = "static/"
if IS_LOCAL_DEV:
    STATIC_ROOT = BASE_DIR / "collected_static"
else:
    STATIC_ROOT = config.getstr("staticfiles.static_root")

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# mail and production erros
if not IS_LOCAL_DEV:
    ROLLBAR = {
        "access_token": "c4ebf44512b4479fb018ee413ac08d2a",
        "environment": "development" if DEBUG else "production",
        "root": BASE_DIR,
    }
    import rollbar

    rollbar.init(**ROLLBAR)

    ANYMAIL = {
        "MAILGUN_API_KEY": config.getstr("mail.api_key"),
        "MAILGUN_SENDER_DOMAIN": "mail.telescoop.fr",
    }
    EMAIL_BACKEND = "anymail.backends.mailgun.EmailBackend"
    DEFAULT_FROM_EMAIL = "no-reply@telescoop.fr"
    SERVER_EMAIL = "no-reply@telescoop.fr"

# CORS
if IS_LOCAL_DEV:
    CORS_ALLOW_ALL_ORIGINS = True

# django-hijack
HIJACK_ALLOW_GET_REQUESTS = True
