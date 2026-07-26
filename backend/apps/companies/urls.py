"""Company and note routes, mounted at ``/api/``."""

from rest_framework.routers import DefaultRouter

from apps.companies.views import CompanyViewSet, NoteViewSet

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("notes", NoteViewSet, basename="note")

urlpatterns = router.urls
