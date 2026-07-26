"""Test settings: fast, isolated, and free of external dependencies."""

from .base import *  # noqa: F403
from .base import REST_FRAMEWORK

DEBUG = False

# Throttling stays wired up (so the code path is exercised) but with limits high
# enough that ordinary tests never trip it. The dedicated throttling test lowers
# the rates explicitly via override_settings.
REST_FRAMEWORK = {
    **REST_FRAMEWORK,
    "DEFAULT_THROTTLE_RATES": {
        "auth_login": "1000/min",
        "auth_register": "1000/min",
        "auth_password": "1000/min",
    },
}

# In-memory SQLite keeps the suite fast and independent of the developer's
# DATABASE_URL.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "ATOMIC_REQUESTS": True,
    }
}

# Hashing dominates auth test runtime; MD5 is safe here because no test data
# leaves the process.
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# No broker in tests: tasks execute inline and surface their exceptions.
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Crawler: no waiting, and no DNS. Tests use example-domain hostnames that do
# not resolve, so the SSRF guard is bypassed by default here; the tests that
# actually exercise it pass `allow_private=False` explicitly.
CRAWLER_DELAY_SECONDS = 0.0
CRAWLER_ALLOW_PRIVATE_NETWORKS = True
CRAWLER_MAX_PAGES = 25
CRAWLER_MAX_DEPTH = 2
