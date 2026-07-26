"""End-to-end scan orchestration, with the HTTP layer replaced by a fake."""

import pytest

from apps.contacts.models import Contact, ContactClassification
from apps.crawler.models import Page, PageType, Scan, ScanStatus
from apps.crawler.services import scanner
from apps.crawler.tests.fakes import FakeHttpClient, install

pytestmark = pytest.mark.django_db

ROOT = "https://acme-robotics.example.com"

SITE = {
    ROOT: """
        <html><head><title>Acme Robotics</title></head><body>
          <a href="/careers">Careers</a>
          <a href="/contact">Contact us</a>
          <a href="/about">About</a>
          <a href="/pricing">Pricing</a>
          <p>General enquiries: info@acme-robotics.example.com</p>
        </body></html>
    """,
    f"{ROOT}/careers": """
        <html><head><title>Careers</title></head><body>
          <p>Send your CV to <a href="mailto:careers@acme-robotics.example.com">us</a>.</p>
          <p>Or contact recruitment@acme-robotics.example.com</p>
          <a href="/careers/engineering">Engineering roles</a>
        </body></html>
    """,
    f"{ROOT}/contact": """
        <html><head><title>Contact</title></head><body>
          <p>info@acme-robotics.example.com</p>
          <p>support@acme-robotics.example.com</p>
        </body></html>
    """,
    f"{ROOT}/about": "<html><head><title>About</title></head><body>Founded 1999.</body></html>",
    f"{ROOT}/pricing": "<html><head><title>Pricing</title></head><body>From 10.</body></html>",
    f"{ROOT}/careers/engineering": """
        <html><head><title>Engineering</title></head><body>
          <p>hiring@acme-robotics.example.com</p>
        </body></html>
    """,
}


@pytest.fixture
def scan(user, company):
    return Scan.objects.create(user=user, company=company, target_url=company.website)


@pytest.fixture
def site(monkeypatch):
    return install(monkeypatch, FakeHttpClient(dict(SITE)))


class TestSuccessfulScan:
    def test_completes(self, scan, site):
        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.COMPLETED
        assert result.started_at is not None
        assert result.finished_at is not None
        assert result.error_message == ""
        assert result.progress_percent == 100

    def test_records_every_page_it_visited(self, scan, site):
        scanner.run_scan(scan_id=scan.pk)

        urls = set(Page.objects.filter(scan=scan).values_list("url", flat=True))
        assert ROOT in urls
        assert f"{ROOT}/careers" in urls
        assert f"{ROOT}/contact" in urls

    def test_classifies_pages(self, scan, site):
        scanner.run_scan(scan_id=scan.pk)

        types = dict(Page.objects.filter(scan=scan).values_list("url", "page_type"))
        assert types[ROOT] == PageType.HOME
        assert types[f"{ROOT}/careers"] == PageType.CAREERS
        assert types[f"{ROOT}/contact"] == PageType.CONTACT
        assert types[f"{ROOT}/about"] == PageType.ABOUT

    def test_visits_recruitment_pages_before_generic_ones(self, scan, site):
        scanner.run_scan(scan_id=scan.pk)

        order = site.requested
        assert order[0] == ROOT
        assert order.index(f"{ROOT}/careers") < order.index(f"{ROOT}/about")
        assert order.index(f"{ROOT}/careers") < order.index(f"{ROOT}/pricing")

    def test_creates_classified_contacts(self, scan, site, company):
        scanner.run_scan(scan_id=scan.pk)

        found = dict(
            Contact.objects.filter(company=company).values_list("email", "classification")
        )
        assert found["careers@acme-robotics.example.com"] == ContactClassification.CAREERS
        assert found["recruitment@acme-robotics.example.com"] == ContactClassification.RECRUITMENT
        assert found["info@acme-robotics.example.com"] == ContactClassification.GENERAL
        assert found["support@acme-robotics.example.com"] == ContactClassification.SUPPORT

    def test_stores_the_source_page_for_each_contact(self, scan, site, company):
        scanner.run_scan(scan_id=scan.pk)

        contact = Contact.objects.get(email="careers@acme-robotics.example.com")
        assert contact.source_url == f"{ROOT}/careers"
        assert contact.source_page is not None
        assert contact.company == company
        assert contact.user == scan.user

    def test_does_not_store_a_duplicate_email_twice(self, scan, site, company):
        # info@ appears on both the homepage and the contact page.
        scanner.run_scan(scan_id=scan.pk)

        assert (
            Contact.objects.filter(
                company=company, email="info@acme-robotics.example.com"
            ).count()
            == 1
        )

    def test_counters_are_consistent(self, scan, site):
        result = scanner.run_scan(scan_id=scan.pk)

        assert result.pages_scanned == Page.objects.filter(scan=scan).count()
        assert result.contacts_found == Contact.objects.filter(company=scan.company).count()
        assert result.pages_discovered >= result.pages_scanned

    def test_a_second_scan_adds_no_duplicate_contacts(self, scan, user, company, site):
        scanner.run_scan(scan_id=scan.pk)
        first_count = Contact.objects.filter(company=company).count()

        second = Scan.objects.create(user=user, company=company, target_url=company.website)
        result = scanner.run_scan(scan_id=second.pk)

        assert Contact.objects.filter(company=company).count() == first_count
        assert result.contacts_found == 0


class TestLimits:
    def test_respects_the_page_budget(self, scan, monkeypatch, settings):
        settings.CRAWLER_MAX_PAGES = 2
        install(monkeypatch, FakeHttpClient(dict(SITE)))

        result = scanner.run_scan(scan_id=scan.pk)

        assert result.pages_scanned == 2

    def test_respects_the_depth_limit(self, scan, monkeypatch, settings):
        settings.CRAWLER_MAX_DEPTH = 1
        client = install(monkeypatch, FakeHttpClient(dict(SITE)))

        scanner.run_scan(scan_id=scan.pk)

        # /careers/engineering is only linked from /careers, i.e. depth 2.
        assert f"{ROOT}/careers/engineering" not in client.requested

    def test_depth_two_reaches_nested_pages(self, scan, site, settings):
        settings.CRAWLER_MAX_DEPTH = 2

        scanner.run_scan(scan_id=scan.pk)

        assert Contact.objects.filter(email="hiring@acme-robotics.example.com").exists()

    def test_skips_pages_disallowed_by_robots(self, scan, monkeypatch):
        client = install(
            monkeypatch,
            FakeHttpClient(dict(SITE), disallowed={f"{ROOT}/careers"}),
        )

        scanner.run_scan(scan_id=scan.pk)

        assert f"{ROOT}/careers" not in client.requested
        assert not Contact.objects.filter(email="careers@acme-robotics.example.com").exists()


class TestFailureHandling:
    def test_unreachable_homepage_fails_the_scan(self, scan, monkeypatch):
        install(monkeypatch, FakeHttpClient({}, failing={ROOT}))

        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.FAILED
        assert result.error_message
        assert result.finished_at is not None

    def test_a_broken_inner_page_does_not_fail_the_scan(self, scan, monkeypatch):
        install(monkeypatch, FakeHttpClient(dict(SITE), failing={f"{ROOT}/about"}))

        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.COMPLETED
        # The attempt is still recorded, with no status code.
        broken = Page.objects.get(scan=scan, url=f"{ROOT}/about")
        assert broken.status_code is None

    def test_contacts_from_working_pages_survive_a_broken_page(self, scan, monkeypatch):
        install(monkeypatch, FakeHttpClient(dict(SITE), failing={f"{ROOT}/contact"}))

        scanner.run_scan(scan_id=scan.pk)

        assert Contact.objects.filter(email="careers@acme-robotics.example.com").exists()

    def test_a_site_with_no_emails_completes_with_no_contacts(self, scan, monkeypatch):
        install(monkeypatch, FakeHttpClient({ROOT: "<html><body>Nothing</body></html>"}))

        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.COMPLETED
        assert result.contacts_found == 0

    def test_running_a_finished_scan_again_is_a_no_op(self, scan, site):
        scanner.run_scan(scan_id=scan.pk)
        pages_before = Page.objects.filter(scan=scan).count()

        # Simulates a task delivered twice.
        result = scanner.run_scan(scan_id=scan.pk)

        assert result.status == ScanStatus.COMPLETED
        assert Page.objects.filter(scan=scan).count() == pages_before


class TestStartScan:
    def test_creates_a_pending_scan(self, user, company):
        scan = scanner.start_scan(user=user, company=company)

        assert scan.status == ScanStatus.PENDING
        assert scan.target_url == company.website
        assert scan.user == user

    def test_refuses_a_second_concurrent_scan(self, user, company):
        scanner.start_scan(user=user, company=company)

        with pytest.raises(scanner.ScanAlreadyRunningError):
            scanner.start_scan(user=user, company=company)

    def test_allows_a_new_scan_once_the_previous_finished(self, user, company, site):
        first = scanner.start_scan(user=user, company=company)
        scanner.run_scan(scan_id=first.pk)

        second = scanner.start_scan(user=user, company=company)

        assert second.pk != first.pk

    def test_rejects_an_unscannable_website(self, user, company, settings):
        settings.CRAWLER_ALLOW_PRIVATE_NETWORKS = False
        company.website = "http://127.0.0.1:8000"
        company.save(update_fields=["website"])

        with pytest.raises(scanner.InvalidScanTargetError):
            scanner.start_scan(user=user, company=company)

        assert Scan.objects.count() == 0
