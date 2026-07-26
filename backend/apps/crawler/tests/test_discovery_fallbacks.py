"""Discovery for sites that link-following alone cannot reach.

The motivating real-world case: a site whose header renders
``<button>Careers</button>`` with a JavaScript click handler and no anchor.
The careers page is public, indexed, and contains a recruitment address, but
there is no ``<a href>`` anywhere in the HTML that points at it.
"""

import pytest

from apps.contacts.models import Contact
from apps.crawler.models import Page, PageType, Scan, ScanStatus
from apps.crawler.services import scanner
from apps.crawler.services.discovery import probe_candidates
from apps.crawler.tests.fakes import FakeHttpClient, install

pytestmark = pytest.mark.django_db

ROOT = "https://acme-robotics.example.com"

# A homepage that navigates with buttons: no links to anything useful.
JS_NAV_HOME = """
<html><head><title>Acme</title></head><body>
  <nav>
    <button><span>Careers</span></button>
    <button><span>Contact</span></button>
  </nav>
  <a href="https://twitter.com/acme">Twitter</a>
  <a href="mailto:hello@acme-robotics.example.com">Email</a>
  <p>hello@acme-robotics.example.com</p>
</body></html>
"""

CAREERS_PAGE = """
<html><head><title>Careers</title></head><body>
  <p>Send your CV to <a href="mailto:careers@acme-robotics.example.com">us</a>.</p>
</body></html>
"""

CONTACT_PAGE = """
<html><head><title>Contact</title></head><body>
  <p>hr@acme-robotics.example.com</p>
</body></html>
"""


@pytest.fixture
def scan(user, company):
    return Scan.objects.create(user=user, company=company, target_url=company.website)


class TestProbeCandidates:
    def test_probes_only_missing_page_types(self):
        candidates = probe_candidates(ROOT, already_found={PageType.CAREERS, PageType.CONTACT})
        types = {candidate.page_type for candidate in candidates}

        assert PageType.CAREERS not in types
        assert PageType.CONTACT not in types
        assert PageType.JOBS in types

    def test_probes_nothing_when_everything_was_found(self):
        found = {
            PageType.CAREERS,
            PageType.JOBS,
            PageType.CONTACT,
            PageType.TEAM,
            PageType.ABOUT,
        }

        assert probe_candidates(ROOT, already_found=found) == []

    def test_candidates_are_marked_speculative(self):
        candidates = probe_candidates(ROOT, already_found=set())

        assert candidates
        assert all(candidate.speculative for candidate in candidates)

    def test_recruitment_paths_come_first(self):
        candidates = probe_candidates(ROOT, already_found=set())

        assert candidates[0].page_type == PageType.CAREERS


class TestSitemapDiscovery:
    def test_finds_pages_the_homepage_never_links_to(self, scan, monkeypatch):
        install(
            monkeypatch,
            FakeHttpClient(
                {
                    ROOT: JS_NAV_HOME,
                    f"{ROOT}/careers": CAREERS_PAGE,
                    f"{ROOT}/contact": CONTACT_PAGE,
                },
                text_resources={
                    f"{ROOT}/sitemap.xml": f"""<?xml version="1.0"?>
                    <urlset>
                      <url><loc>{ROOT}/</loc></url>
                      <url><loc>{ROOT}/careers</loc></url>
                      <url><loc>{ROOT}/contact</loc></url>
                    </urlset>""",
                },
            ),
        )

        scanner.run_scan(scan_id=scan.pk)

        emails = set(Contact.objects.values_list("email", flat=True))
        assert "careers@acme-robotics.example.com" in emails
        assert "hr@acme-robotics.example.com" in emails

    def test_reads_the_sitemap_named_in_robots_txt(self, scan, monkeypatch):
        client = install(
            monkeypatch,
            FakeHttpClient(
                {ROOT: JS_NAV_HOME, f"{ROOT}/careers": CAREERS_PAGE},
                text_resources={
                    f"{ROOT}/robots.txt": f"User-agent: *\nSitemap: {ROOT}/custom-sitemap.xml\n",
                    f"{ROOT}/custom-sitemap.xml": (
                        f"<urlset><url><loc>{ROOT}/careers</loc></url></urlset>"
                    ),
                },
            ),
        )

        scanner.run_scan(scan_id=scan.pk)

        assert f"{ROOT}/custom-sitemap.xml" in client.text_requested
        assert Contact.objects.filter(email="careers@acme-robotics.example.com").exists()

    def test_offsite_sitemap_entries_are_ignored(self, scan, monkeypatch):
        client = install(
            monkeypatch,
            FakeHttpClient(
                {ROOT: JS_NAV_HOME},
                text_resources={
                    f"{ROOT}/sitemap.xml": (
                        "<urlset>"
                        "<url><loc>https://evil.example/pwned</loc></url>"
                        "</urlset>"
                    ),
                },
            ),
        )

        scanner.run_scan(scan_id=scan.pk)

        assert not any("evil.example" in url for url in client.requested)


class TestPathProbing:
    def test_finds_the_careers_page_with_no_sitemap_and_no_links(self, scan, monkeypatch):
        # The exact real-world failure: JavaScript navigation, no sitemap.
        install(
            monkeypatch,
            FakeHttpClient(
                {
                    ROOT: JS_NAV_HOME,
                    f"{ROOT}/careers": CAREERS_PAGE,
                    f"{ROOT}/contact": CONTACT_PAGE,
                }
            ),
        )

        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.COMPLETED
        emails = set(Contact.objects.values_list("email", flat=True))
        assert "careers@acme-robotics.example.com" in emails
        assert "hr@acme-robotics.example.com" in emails

    def test_missed_probes_are_not_recorded_as_pages(self, scan, monkeypatch):
        install(monkeypatch, FakeHttpClient({ROOT: JS_NAV_HOME, f"{ROOT}/careers": CAREERS_PAGE}))

        scanner.run_scan(scan_id=scan.pk)

        recorded = set(Page.objects.filter(scan=scan).values_list("url", flat=True))
        # /jobs, /team, /about etc. do not exist and must not clutter the report.
        assert recorded == {ROOT, f"{ROOT}/careers"}
        assert not Page.objects.filter(scan=scan, status_code__isnull=True).exists()

    def test_missed_probes_do_not_consume_the_page_budget(self, scan, monkeypatch, settings):
        settings.CRAWLER_MAX_PAGES = 2
        install(
            monkeypatch,
            FakeHttpClient(
                {
                    ROOT: JS_NAV_HOME,
                    f"{ROOT}/careers": CAREERS_PAGE,
                    f"{ROOT}/contact": CONTACT_PAGE,
                }
            ),
        )

        result = scanner.run_scan(scan_id=scan.pk)

        # Two real pages, despite many failed probes in between.
        assert result.pages_scanned == 2

    def test_a_linked_site_is_not_probed_for_types_it_already_has(self, scan, monkeypatch):
        linked_home = """
        <html><body>
          <a href="/careers">Careers</a>
          <a href="/contact">Contact</a>
          <a href="/about">About</a>
          <a href="/team">Team</a>
          <a href="/jobs">Jobs</a>
        </body></html>
        """
        client = install(
            monkeypatch,
            FakeHttpClient(
                {
                    ROOT: linked_home,
                    f"{ROOT}/careers": CAREERS_PAGE,
                    f"{ROOT}/contact": CONTACT_PAGE,
                    f"{ROOT}/about": "<html><body>About</body></html>",
                    f"{ROOT}/team": "<html><body>Team</body></html>",
                    f"{ROOT}/jobs": "<html><body>Jobs</body></html>",
                }
            ),
        )

        scanner.run_scan(scan_id=scan.pk)

        # Everything was linked, so no guessed URL should have been requested.
        assert f"{ROOT}/join-us" not in client.requested
        assert f"{ROOT}/vacancies" not in client.requested
