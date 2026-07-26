"""Email extraction from HTML.

Test addresses use the ``.example`` reserved TLD rather than ``example.com`` /
``example.org``: those are on the extractor's placeholder blocklist precisely
because template markup is full of them, so they cannot be used to test the
happy path.
"""

import pytest

from apps.crawler.services.extraction import extract_emails


def page(body: str) -> str:
    return f"<html><head><title>T</title></head><body>{body}</body></html>"


class TestFindsAddresses:
    def test_finds_a_mailto_link(self):
        html = page('<a href="mailto:careers@acme.example">Careers</a>')

        assert extract_emails(html) == ["careers@acme.example"]

    def test_finds_plain_text_addresses(self):
        html = page("<p>Write to hello@acme.example or jobs@acme.example.</p>")

        assert extract_emails(html) == ["hello@acme.example", "jobs@acme.example"]

    def test_strips_mailto_query_parameters(self):
        html = page('<a href="mailto:hr@acme.example?subject=Hello%20there">HR</a>')

        assert extract_emails(html) == ["hr@acme.example"]

    def test_handles_multiple_recipients_in_one_mailto(self):
        html = page('<a href="mailto:a@acme.example,b@acme.example">Mail us</a>')

        assert extract_emails(html) == ["a@acme.example", "b@acme.example"]

    def test_lower_cases_addresses(self):
        html = page("<p>Careers@Acme.EXAMPLE</p>")

        assert extract_emails(html) == ["careers@acme.example"]

    def test_deduplicates(self):
        html = page(
            '<a href="mailto:hr@acme.example">HR</a><p>hr@acme.example and HR@ACME.EXAMPLE</p>'
        )

        assert extract_emails(html) == ["hr@acme.example"]

    def test_mailto_links_come_first(self):
        html = page('<p>text@acme.example</p><a href="mailto:link@acme.example">L</a>')

        assert extract_emails(html) == ["link@acme.example", "text@acme.example"]

    def test_handles_dotted_and_plus_addresses(self):
        html = page("<p>first.last+jobs@sub.acme.example</p>")

        assert extract_emails(html) == ["first.last+jobs@sub.acme.example"]

    def test_strips_trailing_punctuation(self):
        html = page("<p>Contact careers@acme.example.</p>")

        assert extract_emails(html) == ["careers@acme.example"]


class TestIgnoresNoise:
    def test_ignores_script_and_style_blocks(self):
        html = page(
            "<script>var t='tracker@analytics.example';</script>"
            "<style>/* build@assets.example */</style>"
            "<p>real@acme.example</p>"
        )

        assert extract_emails(html) == ["real@acme.example"]

    @pytest.mark.parametrize(
        ("text", "reason"),
        [
            ("logo@2x.png", "image sprite"),
            ("sprite@3x.jpg", "image sprite"),
            ("noreply@example.com", "reserved placeholder domain"),
            ("hr@example.org", "reserved placeholder domain"),
            ("you@yourdomain.com", "template placeholder domain"),
            ("name@domain.com", "template placeholder domain"),
            ("email@acme.example", "template placeholder local part"),
            ("yourname@acme.example", "template placeholder local part"),
        ],
    )
    def test_drops_placeholders_and_assets(self, text, reason):
        assert extract_emails(page(f"<p>{text}</p>")) == [], reason

    def test_ignores_text_without_addresses(self):
        assert extract_emails(page("<p>Nothing here at all.</p>")) == []

    def test_ignores_malformed_addresses(self):
        html = page("<p>not@ an@address @acme.example bad@@acme.example</p>")

        assert extract_emails(html) == []

    def test_handles_empty_html(self):
        assert extract_emails("") == []


class TestRealisticPage:
    def test_extracts_from_a_careers_page(self):
        html = page(
            """
            <h1>Work with us</h1>
            <p>Send your CV to <a href="mailto:careers@acme.example">careers@acme.example</a>.</p>
            <p>Press enquiries: press@acme.example</p>
            <footer>
              <a href="mailto:info@acme.example">General enquiries</a>
              <img src="logo@2x.png">
              <script>window.key='abc@cdn.example';</script>
            </footer>
            """
        )

        assert extract_emails(html) == [
            "careers@acme.example",
            "info@acme.example",
            "press@acme.example",
        ]
