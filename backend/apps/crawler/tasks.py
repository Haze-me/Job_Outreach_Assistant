"""Celery tasks for the crawler."""

import logging

from celery import shared_task

from apps.crawler.services import scanner

logger = logging.getLogger(__name__)


@shared_task(name="crawler.run_company_scan", bind=True, ignore_result=False)
def run_company_scan(self, scan_id: str) -> dict:
    """Runs one website scan.

    No automatic retry: ``run_scan`` already records failures on the scan
    record, and silently re-crawling a third-party website because it was
    briefly unreachable is not polite behaviour. The user can start a new scan.
    """
    scan = scanner.run_scan(scan_id=scan_id)
    return {
        "scan_id": str(scan.pk),
        "status": scan.status,
        "pages_scanned": scan.pages_scanned,
        "contacts_found": scan.contacts_found,
    }
