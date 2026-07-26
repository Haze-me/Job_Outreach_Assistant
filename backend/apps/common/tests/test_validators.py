"""Tests for website URL normalisation."""

import pytest
from django.core.exceptions import ValidationError

from apps.common.validators import normalize_website_url


class TestNormalizeWebsiteUrl:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [
            ("example.com", "https://example.com"),
            ("  example.com  ", "https://example.com"),
            ("https://example.com/", "https://example.com"),
            ("HTTPS://EXAMPLE.COM", "https://example.com"),
            ("http://Example.com", "http://example.com"),
            ("https://example.com:443", "https://example.com"),
            ("http://example.com:80", "http://example.com"),
            ("https://example.com:8443", "https://example.com:8443"),
            ("https://example.com/careers/", "https://example.com/careers"),
            ("https://example.com/#team", "https://example.com"),
            ("https://example.com/jobs?ref=x", "https://example.com/jobs?ref=x"),
            ("https://www.example.co.uk", "https://www.example.co.uk"),
            ("https://example.com.", "https://example.com"),
        ],
    )
    def test_normalises(self, raw, expected):
        assert normalize_website_url(raw) == expected

    def test_strips_embedded_credentials(self):
        # Credentials in a stored URL would leak on every scan request.
        assert normalize_website_url("https://user:pw@example.com") == "https://example.com"

    @pytest.mark.parametrize(
        "raw",
        [
            "",
            "   ",
            "ftp://example.com",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "localhost",
            "http://localhost:8000",
            "https://nodots",
            "not a url at all",
        ],
    )
    def test_rejects(self, raw):
        with pytest.raises(ValidationError):
            normalize_website_url(raw)

    def test_rejects_none(self):
        with pytest.raises(ValidationError):
            normalize_website_url(None)
