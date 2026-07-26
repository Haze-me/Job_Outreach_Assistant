"""User routes.

Mounted under ``/api/auth/`` because the specification groups profile
management inside the Authentication module. The app still owns its own
routes, so nothing outside this file needs to change when they grow.
"""

from django.urls import path

from apps.users.views import ProfileView

urlpatterns = [
    path("profile/", ProfileView.as_view(), name="profile"),
]
