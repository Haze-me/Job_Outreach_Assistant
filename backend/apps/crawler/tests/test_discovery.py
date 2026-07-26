"""Page classification and internal link discovery."""

import pytest

from apps.crawler.models import PageType
from apps.crawler.services.discovery import (
    classify_page_type,
    discover_links,
    is_same_site,
    normalize_link,
)

ROOT = "https://acme.example"


class TestClassifyPageType:
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            (f"{ROOT}/", PageType.HOME),
            (f"{ROOT}", PageType.HOME),
            (f"{ROOT}/index.html", PageType.HOME),
            (f"{ROOT}/careers", PageType.CAREERS),
            (f"{ROOT}/work-with-us", PageType.CAREERS),
            (f"{ROOT}/join-us", PageType.CAREERS),
            (f"{ROOT}/jobs", PageType.JOBS),
            (f"{ROOT}/vacancies", PageType.JOBS),
            (f"{ROOT}/contact", PageType.CONTACT),
            (f"{ROOT}/get-in-touch", PageType.CONTACT),
            (f"{ROOT}/about", PageType.ABOUT),
            (f"{ROOT}/who-we-are", PageType.ABOUT),
            (f"{ROOT}/team", PageType.TEAM),
            (f"{ROOT}/our-people", PageType.TEAM),
            (f"{ROOT}/leadership", PageType.LEADERSHIP),
            (f"{ROOT}/board", PageType.LEADERSHIP),
            (f"{ROOT}/press", PageType.PRESS),
            (f"{ROOT}/newsroom", PageType.PRESS),
            (f"{ROOT}/pricing", PageType.OTHER),
            (f"{ROOT}/blog/some-post", PageType.OTHER),
        ],
    )
    def test_classifies_by_path(self, url, expected):
        assert classify_page_type(url) == expected

    def test_link_text_is_used_as_a_fallback(self):
        assert classify_page_type(f"{ROOT}/x7", "Careers at Acme") == PageType.CAREERS

    def test_more_specific_type_wins(self):
        # /about/careers is a careers page, not an about page.
        assert classify_page_type(f"{ROOT}/about/careers") == PageType.CAREERS

    def test_keyword_needs_a_word_boundary(self):
        assert classify_page_type(f"{ROOT}/jobsworth-blog") == PageType.OTHER
        assert classify_page_type(f"{ROOT}/aboutique") == PageType.OTHER


class TestIsSameSite:
    @pytest.mark.parametrize(
        "url",
        [
            f"{ROOT}/careers",
            "https://www.acme.example/careers",
            "https://careers.acme.example/",  # jobs often live on a subdomain
            "http://acme.example/contact",
        ],
    )
    def test_same_site(self, url):
        assert is_same_site(url, ROOT) is True

    @pytest.mark.parametrize(
        "url",
        [
            "https://other.example/careers",
            "https://linkedin.com/company/acme",
            "https://twitter.com/acme",
            "https://facebook.com/acme",
            "https://github.com/acme",
        ],
    )
    def test_different_site_or_social(self, url):
        assert is_same_site(url, ROOT) is False


class TestNormalizeLink:
    @pytest.mark.parametrize(
        ("href", "expected"),
        [
            ("/careers", f"{ROOT}/careers"),
            ("careers", f"{ROOT}/careers"),
            (f"{ROOT}/careers/", f"{ROOT}/careers"),
            ("/careers#apply", f"{ROOT}/careers"),
            ("//acme.example/jobs", "https://acme.example/jobs"),
        ],
    )
    def test_normalises(self, href, expected):
        assert normalize_link(href, f"{ROOT}/") == expected

    @pytest.mark.parametrize(
        "href",
        ["", "#", "#section", "mailto:a@b.example", "tel:+353", "javascript:void(0)", "data:x"],
    )
    def test_rejects_non_navigational_hrefs(self, href):
        assert normalize_link(href, f"{ROOT}/") is None


class TestDiscoverLinks:
    HOMEPAGE = """
    <html><body>
      <a href="/about">About us</a>
      <a href="/careers">Careers</a>
      <a href="/contact">Contact</a>
      <a href="/jobs">Open roles</a>
      <a href="/team">Our team</a>
      <a href="/pricing">Pricing</a>
      <a href="https://twitter.com/acme">Twitter</a>
      <a href="https://unrelated.example/x">Partner</a>
      <a href="/brochure.pdf">Brochure</a>
      <a href="/wp-admin/">Admin</a>
      <a href="mailto:hi@acme.example">Email</a>
    </body></html>
    """

    def test_finds_only_internal_html_pages(self):
        links = discover_links(self.HOMEPAGE, f"{ROOT}/", ROOT, depth=1)
        urls = {link.url for link in links}

        assert urls == {
            f"{ROOT}/about",
            f"{ROOT}/careers",
            f"{ROOT}/contact",
            f"{ROOT}/jobs",
            f"{ROOT}/team",
            f"{ROOT}/pricing",
        }

    def test_orders_recruitment_pages_first(self):
        links = discover_links(self.HOMEPAGE, f"{ROOT}/", ROOT, depth=1)

        assert [link.url for link in links][:3] == [
            f"{ROOT}/careers",
            f"{ROOT}/jobs",
            f"{ROOT}/contact",
        ]

    def test_skips_assets_admin_and_social(self):
        urls = {link.url for link in discover_links(self.HOMEPAGE, f"{ROOT}/", ROOT, depth=1)}

        assert not any("brochure.pdf" in url for url in urls)
        assert not any("wp-admin" in url for url in urls)
        assert not any("twitter.com" in url for url in urls)

    def test_deduplicates_and_keeps_the_best_classification(self):
        html = """
        <a href="/careers">Read more</a>
        <a href="/careers">Careers</a>
        """
        links = discover_links(html, f"{ROOT}/", ROOT, depth=1)

        assert len(links) == 1
        assert links[0].page_type == PageType.CAREERS

    def test_records_the_given_depth(self):
        links = discover_links(self.HOMEPAGE, f"{ROOT}/", ROOT, depth=2)

        assert all(link.depth == 2 for link in links)

    def test_handles_a_page_with_no_links(self):
        assert discover_links("<html><body>Nothing</body></html>", f"{ROOT}/", ROOT, depth=1) == []
