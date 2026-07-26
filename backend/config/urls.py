"""Root URL configuration.

Domain routes live in each app's ``urls.py`` and are mounted here under
``/api/``. Adding a module means adding one line, never editing existing ones.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.common.views import HealthCheckView

api_patterns = [
    path("health/", HealthCheckView.as_view(), name="health-check"),
    # Authentication surface. Two modules share the /auth/ prefix: the
    # authentication app owns credential operations, while the users app owns
    # the profile resource. Each app keeps its own urls.py, so neither has to
    # import from the other.
    path("auth/", include("apps.authentication.urls")),
    path("auth/", include("apps.users.urls")),
    # Domain resources.
    path("", include("apps.companies.urls")),
    path("", include("apps.crawler.urls")),
    path("", include("apps.contacts.urls")),
    path("", include("apps.applications.urls")),
    path("", include("apps.dashboard.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include((api_patterns, "api"))),
    # OpenAPI schema and interactive documentation.
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path(
        "api/redoc/",
        SpectacularRedocView.as_view(url_name="schema"),
        name="redoc",
    ),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
