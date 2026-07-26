"""Contact routes, mounted at ``/api/``."""

from rest_framework.routers import DefaultRouter

from apps.contacts.views import ContactViewSet

router = DefaultRouter()
router.register("contacts", ContactViewSet, basename="contact")

urlpatterns = router.urls
