"""Extraction of deliberately obfuscated email addresses.

Uses the ``.example`` reserved TLD; ``example.com`` and ``example.org`` are on
the extractor's placeholder blocklist.
"""

import pytest

from apps.crawler.services.extraction import decode_cfemail, extract_emails


def page(body: str) -> str:
    return f"<html><head><title>T</title></head><body>{body}</body></html>"


def encode_cfemail(email: str, key: int = 0x7A) -> str:
    """Builds a Cloudflare-encoded value, mirroring their scheme."""
    return f"{key:02x}" + "".join(f"{ord(char) ^ key:02x}" for char in email)


class TestCloudflareDecoding:
    def test_round_trips(self):
        assert decode_cfemail(encode_cfemail("careers@acme.example")) == "careers@acme.example"

    @pytest.mark.parametrize("key", [0x00, 0x01, 0x5F, 0xA3, 0xFF])
    def test_works_for_any_key(self, key):
        encoded = encode_cfemail("hr@acme.example", key=key)

        assert decode_cfemail(encoded) == "hr@acme.example"

    @pytest.mark.parametrize("value", ["", "zz", "7", "not-hex", "7a"])
    def test_rejects_malformed_input(self, value):
        assert decode_cfemail(value) is None

    def test_extracts_from_a_data_cfemail_span(self):
        encoded = encode_cfemail("careers@acme.example")
        html = page(
            f'<span class="__cf_email__" data-cfemail="{encoded}">[email&#160;protected]</span>'
        )

        assert extract_emails(html) == ["careers@acme.example"]

    def test_extracts_from_a_protected_mailto_href(self):
        encoded = encode_cfemail("recruitment@acme.example")
        html = page(f'<a href="/cdn-cgi/l/email-protection#{encoded}">Email us</a>')

        assert extract_emails(html) == ["recruitment@acme.example"]

    def test_a_protected_page_is_not_empty(self):
        # Without decoding, this page yields nothing at all -- which is exactly
        # what made Cloudflare-protected sites look contact-free.
        encoded = encode_cfemail("hr@acme.example")
        html = page(
            '<p>Contact: <a class="__cf_email__" '
            f'data-cfemail="{encoded}" href="/cdn-cgi/l/email-protection">[email protected]</a></p>'
        )

        assert extract_emails(html) == ["hr@acme.example"]

    def test_deduplicates_against_the_plain_form(self):
        encoded = encode_cfemail("careers@acme.example")
        html = page(
            f'<span data-cfemail="{encoded}">x</span><p>careers@acme.example</p>'
        )

        assert extract_emails(html) == ["careers@acme.example"]


class TestTextObfuscation:
    @pytest.mark.parametrize(
        "text",
        [
            "careers [at] acme [dot] example",
            "careers (at) acme (dot) example",
            "careers {at} acme {dot} example",
            "careers [AT] acme [DOT] example",
            "careers [at] acme.example",
            "careers[at]acme[dot]example",
            "careers -at- acme -dot- example",
        ],
    )
    def test_reassembles_common_forms(self, text):
        assert extract_emails(page(f"<p>{text}</p>")) == ["careers@acme.example"]

    def test_handles_a_multi_level_domain(self):
        html = page("<p>hr [at] jobs [dot] acme [dot] example</p>")

        assert extract_emails(html) == ["hr@jobs.acme.example"]

    def test_handles_a_dotted_local_part(self):
        html = page("<p>first.last [at] acme [dot] example</p>")

        assert extract_emails(html) == ["first.last@acme.example"]


class TestNoFalsePositives:
    """The failure mode to avoid is inventing addresses that do not exist."""

    @pytest.mark.parametrize(
        "text",
        [
            # Ordinary English. A bare "at" must never be treated as "@".
            "Contact us at acme.example for more information.",
            "Our office is at 12 Main Street, Dublin.",
            "Look at our.work portfolio",
            "Available at any.time",
        ],
    )
    def test_bare_at_is_not_an_address(self, text):
        assert extract_emails(page(f"<p>{text}</p>")) == []

    def test_prose_around_a_real_obfuscated_address_still_works(self):
        html = page(
            "<p>Send your CV to careers [at] acme [dot] example — "
            "our office is at 12 Main Street.</p>"
        )

        assert extract_emails(html) == ["careers@acme.example"]

    def test_placeholder_domains_are_still_blocked(self):
        assert extract_emails(page("<p>you [at] yourdomain [dot] com</p>")) == []
