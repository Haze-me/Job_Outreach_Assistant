"""Base settings shared by every environment.

Environment-specific modules (``development``, ``production``, ``test``) import
from here and override only what differs. Nothing secret is hard-coded: all
deployment-varying values are read from the environment via ``django-environ``.
"""

from datetime import timedelta
from pathlib import Path

import environ

# backend/config/settings/base.py -> backend/
BASE_DIR = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = BASE_DIR.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")


# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-development-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "users.User"


# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "drf_spectacular",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.common",
    "apps.users",
    "apps.authentication",
    "apps.companies",
    "apps.crawler",
    "apps.contacts",
    "apps.applications",
    "apps.dashboard",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS


MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
# Driven entirely by DATABASE_URL so moving from SQLite to PostgreSQL is a
# single environment-variable change with no code edits.
#   sqlite:   sqlite:///db.sqlite3
#   postgres: postgres://user:password@localhost:5432/job_outreach
DATABASES = {
    "default": env.db_url(
        "DATABASE_URL",
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
    )
}
DATABASES["default"]["ATOMIC_REQUESTS"] = True
DATABASES["default"].setdefault("CONN_MAX_AGE", env.int("DATABASE_CONN_MAX_AGE", default=60))


# ---------------------------------------------------------------------------
# Password validation & hashing
# ---------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 8},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Argon2 first: memory-hard and the current Django recommendation. PBKDF2 is
# retained so existing hashes remain verifiable and are upgraded on next login.
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]


# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = env("DJANGO_TIME_ZONE", default="UTC")
USE_I18N = True
USE_TZ = True


# ---------------------------------------------------------------------------
# Static & media
# ---------------------------------------------------------------------------
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"


# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    # Secure by default: every endpoint requires auth unless it opts out.
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticated",),
    "DEFAULT_PAGINATION_CLASS": "apps.common.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": env.int("API_PAGE_SIZE", default=20),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "apps.common.exceptions.api_exception_handler",
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    # ScopedRateThrottle only applies to views that declare a `throttle_scope`,
    # so unscoped endpoints are unaffected. Used to blunt credential-stuffing
    # and registration-spam against the auth endpoints.
    "DEFAULT_THROTTLE_CLASSES": ("rest_framework.throttling.ScopedRateThrottle",),
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": env("THROTTLE_AUTH_LOGIN", default="10/min"),
        "auth_register": env("THROTTLE_AUTH_REGISTER", default="20/hour"),
        "auth_password": env("THROTTLE_AUTH_PASSWORD", default="10/hour"),
    },
}


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=env.int("JWT_ACCESS_MINUTES", default=15)),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=env.int("JWT_REFRESH_DAYS", default=7)),
    # Rotation + blacklisting means a stolen refresh token is usable at most
    # once, and logout can genuinely invalidate a session.
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": SECRET_KEY,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    # Adds the serialised user to the login response and normalises the email
    # before authentication.
    "TOKEN_OBTAIN_PAIR_SERIALIZER": "apps.authentication.serializers.LoginSerializer",
}


SPECTACULAR_SETTINGS = {
    "TITLE": "Job Outreach Assistant API",
    "DESCRIPTION": (
        "REST API for discovering publicly available recruitment contacts on "
        "company websites and tracking job applications."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api",
    "SORT_OPERATIONS": False,
    # Several models expose a field called `status`. Naming each choice set
    # explicitly keeps the generated client types readable instead of
    # producing collision-suffixed names like `Status92bEnum`.
    "ENUM_NAME_OVERRIDES": {
        "ScanStatusEnum": "apps.crawler.models.ScanStatus.choices",
        "PageTypeEnum": "apps.crawler.models.PageType.choices",
        "ApplicationStatusEnum": "apps.applications.models.ApplicationStatus.choices",
        "ContactClassificationEnum": "apps.contacts.models.ContactClassification.choices",
    },
}


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=["http://localhost:5173", "http://127.0.0.1:5173"],
)
CORS_ALLOW_CREDENTIALS = False  # JWT travels in the Authorization header.


# ---------------------------------------------------------------------------
# Celery
# ---------------------------------------------------------------------------
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default="redis://127.0.0.1:6379/1")
# Eager mode runs tasks inline in the web process. It keeps the application
# fully usable without Redis in development; production must leave it off.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = env.bool("CELERY_TASK_EAGER_PROPAGATES", default=False)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = env.int("CELERY_TASK_TIME_LIMIT", default=600)
CELERY_TASK_SOFT_TIME_LIMIT = env.int("CELERY_TASK_SOFT_TIME_LIMIT", default=540)
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True


# ---------------------------------------------------------------------------
# Website crawler
# ---------------------------------------------------------------------------
# Deliberately conservative. The crawler visits third-party websites we do not
# own, so it identifies itself honestly, obeys robots.txt, waits between
# requests, and stops early rather than exhaustively spidering a site.
CRAWLER_USER_AGENT = env(
    "CRAWLER_USER_AGENT",
    default=(
        "JobOutreachAssistant/1.0 (+contact-discovery; respects robots.txt)"
    ),
)
CRAWLER_REQUEST_TIMEOUT = env.float("CRAWLER_REQUEST_TIMEOUT", default=10.0)
# 40 pages: large marketing sites carry dozens of SEO landing pages, and a
# smaller budget gets spent on those before reaching the careers page.
CRAWLER_MAX_PAGES = env.int("CRAWLER_MAX_PAGES", default=40)
CRAWLER_MAX_DEPTH = env.int("CRAWLER_MAX_DEPTH", default=2)
# Half a second between requests. Still well below the rate an ordinary
# browsing session generates, and it halves the wall-clock time of a scan.
CRAWLER_DELAY_SECONDS = env.float("CRAWLER_DELAY_SECONDS", default=0.5)
CRAWLER_RESPECT_ROBOTS_TXT = env.bool("CRAWLER_RESPECT_ROBOTS_TXT", default=True)
CRAWLER_MAX_RESPONSE_BYTES = env.int("CRAWLER_MAX_RESPONSE_BYTES", default=2_000_000)
CRAWLER_MAX_REDIRECTS = env.int("CRAWLER_MAX_REDIRECTS", default=5)
# Must stay False anywhere the API is reachable by untrusted users: it is the
# switch that disables SSRF protection. Only useful for testing against a local
# fixture server.
CRAWLER_ALLOW_PRIVATE_NETWORKS = env.bool("CRAWLER_ALLOW_PRIVATE_NETWORKS", default=False)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL", default="INFO"),
    },
    "loggers": {
        "django.db.backends": {"level": "INFO", "propagate": True},
        "apps": {
            "handlers": ["console"],
            "level": env("APP_LOG_LEVEL", default="INFO"),
            "propagate": False,
        },
    },
}
