import os
import sentry_sdk
from pathlib import Path
from envparse import env
from sentry_sdk.integrations.django import DjangoIntegration

DEBUG = env.bool("DEBUG")
SERVER_IP = env.str("SERVER_IP")
SECRET_KEY = env.str("SECRET_KEY")
BACKEND_URL = env.str("BACKEND_URL")
ALLOWED_HOSTS = ["localhost", env.str("ALLOWED_HOSTS")]
CSRF_TRUSTED_ORIGINS = [
    f'http://{env.str("ALLOWED_HOSTS")}',
    f'https://{env.str("ALLOWED_HOSTS")}',
]
BASE_DIR = Path(__file__).resolve().parent.parent

LOCAL = "local"
PRODUCTION = "production"
ENVIRONMENT = env.str("ENVIRONMENT", default="local")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "network",
    "telegram",
    "linkedin",
    "twitter",
    "notification",
    "corsheaders",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "social.urls"

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

WSGI_APPLICATION = "social.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": "social_db",
        "NAME": "postgres",
        "PORT": 5432,
        "USER": env.str("POSTGRES_USER"),
        "PASSWORD": env.str("POSTGRES_PASSWORD"),
    },
}

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

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


STATIC_URL = "/static/"
if DEBUG:
    STATICFILES_DIRS = (os.path.join(BASE_DIR, "static"),)
else:
    STATIC_ROOT = os.path.join(BASE_DIR, "static")
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Celery
BROKER_URL = "redis://social_redis:6379"
CELERY_RESULT_BACKEND = "redis://social_redis:6379"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Tehran"


CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOWED_ORIGIN_REGEXES = ["*"]

if (dsn := env.str("SENTRY_DSN", default=None)) is not None:
    sentry_sdk.init(
        dsn=dsn,
        integrations=[DjangoIntegration()],
        traces_sample_rate=1.0,
        send_default_pii=True,
        environment="ras-soc",
    )

# Linkedin account auth
LINKEDIN_EMAIL = env.str("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = env.str("LINKEDIN_PASSWORD")

# Telegram account auth
TELEGRAM_API_ID = env.str("TELEGRAM_API_ID")
TELEGRAM_API_HASH = env.str("TELEGRAM_API_HASH")


CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": "redis://social_redis:6379/15",  # Some db numbers already used
    }
}


# Email Configs
EMAIL_HOST = "smtp-mail.outlook.com"
EMAIL_PORT = 587
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default=None)
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default=None)
EMAIL_USE_TLS = True
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

# Email Logging Configs
ADMIN_EMAIL_LOG = env("ADMIN_EMAIL_LOG", default=None)
ADMINS = (("Log Admin", ADMIN_EMAIL_LOG),)
SERVER_EMAIL = EMAIL_HOST_USER

# Logging (Just Email Handler)
if EMAIL_HOST_USER and ADMIN_EMAIL_LOG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {"format": "%(levelname)s %(message)s"},
        },
        "handlers": {
            "mail_admins": {
                "level": "ERROR",
                "class": "django.utils.log.AdminEmailHandler",
                "formatter": "simple",
            },
            "console": {
                "class": "logging.StreamHandler",
            },
        },
        "loggers": {
            # all modules
            "": {
                "handlers": ["mail_admins", "console"],
                "level": "ERROR",
                "propagate": False,
            },
            "celery": {
                "handlers": ["mail_admins", "console"],
                "level": "ERROR",
                "propagate": False,
            },
        },
    }
