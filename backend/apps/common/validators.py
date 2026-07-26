"""Shared input validation and normalisation helpers."""

from urllib.parse import urlsplit, urlunsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.translation import gettext_lazy as _

ALLOWED_URL_SCHEMES = ("http", "https")

# Hostnames that never identify a public company website. Rejecting them here
# is a usability guard, not a security boundary -- the crawler applies the real
# SSRF protection before making any request.
BLOCKED_HOSTNAMES = frozenset({"localhost", "localhost.localdomain", "ip6-localhost"})


def normalize_website_url(value: str) -> str:
    """Validates a company website and returns it in a canonical form.

    Normalising on the way in means two users typing ``Example.com`` and
    ``https://example.com/`` end up with the same stored value, so duplicate
    detection and scan targeting both behave predictably.

    Applied transformations:
      * surrounding whitespace removed
      * a missing scheme defaults to ``https://``
      * scheme and host lower-cased
      * ``user:password@`` credentials stripped
      * default ports (80/443) removed
      * trailing slash and URL fragment removed
    """
    if not value or not value.strip():
        raise ValidationError(_("Enter a website URL."), code="required")

    url = value.strip()
    if "://" not in url:
        # "example.com/careers" is what people actually type.
        url = f"https://{url}"

    parts = urlsplit(url)

    scheme = parts.scheme.lower()
    if scheme not in ALLOWED_URL_SCHEMES:
        raise ValidationError(
            _("Only http:// and https:// website addresses are supported."),
            code="invalid_scheme",
        )

    # `hostname` drops any userinfo and normalises case for us.
    host = (parts.hostname or "").rstrip(".")
    if not host:
        raise ValidationError(_("Enter a valid website URL."), code="invalid")
    if host in BLOCKED_HOSTNAMES or "." not in host:
        raise ValidationError(
            _("Enter a public company website address."),
            code="invalid_host",
        )

    netloc = host
    try:
        port = parts.port
    except ValueError as exc:  # non-numeric port
        raise ValidationError(_("Enter a valid website URL."), code="invalid") from exc
    if port is not None and port not in (80, 443):
        netloc = f"{host}:{port}"

    normalized = urlunsplit((scheme, netloc, parts.path.rstrip("/"), parts.query, ""))

    # Final syntax check with Django's own validator.
    URLValidator(schemes=list(ALLOWED_URL_SCHEMES))(normalized)
    return normalized
