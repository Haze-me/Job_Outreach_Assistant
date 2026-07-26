"""Page discovery via sitemap.xml.

Following ``<a href>`` links only finds pages the site chose to link in HTML.
Plenty of modern sites navigate with JavaScript -- a React or Next.js header
renders ``<button>Careers</button>`` with a click handler and no anchor at all
-- so a careers page can be completely unreachable to a link-following crawler
even though it is public, indexed, and listed in the site's own sitemap.

The sitemap is the canonical list of a site's public URLs and is unaffected by
how the navigation is built, which makes it the single most reliable discovery
source available without executing JavaScript.
"""

from __future__ import annotations

import logging
import re

from apps.crawler.services.discovery import is_same_site, normalize_link

logger = logging.getLogger(__name__)

# Deliberately regex rather than an XML parser: sitemaps in the wild are often
# malformed, and a namespace-aware parse buys nothing when the only thing
# needed is the <loc> values.
LOC_PATTERN = re.compile(r"<loc>\s*([^<\s]+)\s*</loc>", re.IGNORECASE)
SITEMAP_DIRECTIVE = re.compile(r"^\s*sitemap:\s*(\S+)", re.IGNORECASE | re.MULTILINE)

# A sitemap index points at more sitemaps. Follow a couple, not the whole tree.
MAX_CHILD_SITEMAPS = 3
MAX_URLS = 300


def _candidate_sitemap_urls(client, root_url: str) -> list[str]:
    """Sitemap locations to try, most authoritative first."""
    urls: list[str] = []

    # robots.txt may name the sitemap explicitly, which beats guessing.
    robots = client.get_text(f"{root_url.rstrip('/')}/robots.txt")
    if robots:
        urls.extend(match.group(1).strip() for match in SITEMAP_DIRECTIVE.finditer(robots))

    for fallback in ("/sitemap.xml", "/sitemap_index.xml", "/sitemap-index.xml"):
        candidate = f"{root_url.rstrip('/')}{fallback}"
        if candidate not in urls:
            urls.append(candidate)

    return urls


def discover_sitemap_urls(client, root_url: str, *, limit: int = MAX_URLS) -> list[str]:
    """Returns same-site page URLs listed in the site's sitemap.

    Never raises: a missing or unparseable sitemap is the normal case for a
    great many sites, and the crawl continues on links alone.
    """
    found: list[str] = []
    seen: set[str] = set()
    children_followed = 0

    for sitemap_url in _candidate_sitemap_urls(client, root_url):
        body = client.get_text(sitemap_url)
        if not body:
            continue

        locations = [match.group(1) for match in LOC_PATTERN.finditer(body)]
        if not locations:
            continue

        is_index = "<sitemapindex" in body.lower()
        if is_index:
            # Recurse one level into the child sitemaps.
            for child in locations[:MAX_CHILD_SITEMAPS]:
                children_followed += 1
                child_body = client.get_text(child)
                if not child_body:
                    continue
                locations.extend(
                    match.group(1) for match in LOC_PATTERN.finditer(child_body)
                )
            # After recursing, drop the child-sitemap entries themselves so
            # only real page URLs remain.
            locations = [loc for loc in locations if not loc.lower().endswith(".xml")]

        for location in locations:
            url = normalize_link(location, root_url)
            if not url or url in seen or not is_same_site(url, root_url):
                continue
            seen.add(url)
            found.append(url)
            if len(found) >= limit:
                break

        if found:
            logger.info("Found %s URLs in %s", len(found), sitemap_url)
            break

    return found
