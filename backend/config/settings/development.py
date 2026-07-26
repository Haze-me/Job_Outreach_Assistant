"""Local development settings."""

from .base import *  # noqa: F403
from .base import env  # noqa: F401

DEBUG = env.bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "[::1]"])

# Convenience for local API exploration; the JSON renderer stays first so
# programmatic clients are unaffected.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = (  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
