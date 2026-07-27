"""Scanner routes, mounted at ``/api/``.

The specification writes these paths without a trailing slash, but the rest of
the API uses one. A single regex accepts both rather than registering two
routes: two routes would mean the same operation appearing twice in the OpenAPI
schema. ``APPEND_SLASH`` is not an option here -- its redirect would drop the
body and method of a POST.

``reverse()`` produces the specification's slash-less form.
"""

from django.urls import re_path

from apps.crawler.views import ScanCancelView, ScanCreateView, ScanStatusView

UUID_RE = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"

urlpatterns = [
    re_path(
        rf"^scan/status/(?P<scan_id>{UUID_RE})/?$",
        ScanStatusView.as_view(),
        name="scan-status",
    ),
    # Declared before the scan/<company_id> route so "cancel" is not read as
    # a company id.
    re_path(
        rf"^scan/cancel/(?P<scan_id>{UUID_RE})/?$",
        ScanCancelView.as_view(),
        name="scan-cancel",
    ),
    re_path(
        rf"^scan/(?P<company_id>{UUID_RE})/?$",
        ScanCreateView.as_view(),
        name="scan-create",
    ),
]
