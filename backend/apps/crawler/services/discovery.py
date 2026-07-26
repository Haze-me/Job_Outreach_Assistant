"""Deciding which internal pages a scan should visit.

The specification names the page kinds worth looking at: Home, About, Careers,
Jobs, Contact, Team, Leadership, Press. Rather than spidering a whole site, the
crawler scores links against those categories and visits the best candidates
first, so a 25-page budget is spent on the pages that actually carry
recruitment contacts.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urldefrag, urljoin, urlsplit

from bs4 import BeautifulSoup

from apps.crawler.models import PageType

# Keywords matched against both the URL path and the link text. Ordered most
# specific first: "careers" must win over the generic "about" on a URL like
# /about/careers.
PAGE_TYPE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        PageType.CAREERS,
        ("career", "careers", "work-with-us", "work-for-us", "join-us", "join-our-team", "hiring"),
    ),
    (
        PageType.JOBS,
        ("job", "jobs", "vacancy", "vacancies", "opening", "openings", "opportunities", "recruit"),
    ),
    (
        PageType.CONTACT,
        ("contact", "contact-us", "contactus", "get-in-touch", "reach-us", "enquiries"),
    ),
    (PageType.TEAM, ("team", "our-team", "people", "our-people", "staff", "meet-the-team")),
    (
        PageType.LEADERSHIP,
        ("leadership", "management", "executive", "executives", "board", "founders"),
    ),
    (PageType.PRESS, ("press", "media", "newsroom", "news", "press-releases")),
    (PageType.ABOUT, ("about", "about-us", "aboutus", "who-we-are", "our-story", "company")),
)

# Visit order when the page budget is smaller than the number of candidates.
# Recruitment pages first -- they are why the product exists.
TYPE_PRIORITY: dict[str, int] = {
    PageType.CAREERS: 0,
    PageType.JOBS: 1,
    PageType.CONTACT: 2,
    PageType.TEAM: 3,
    PageType.LEADERSHIP: 4,
    PageType.ABOUT: 5,
    PageType.PRESS: 6,
    PageType.OTHER: 7,
}

# Never worth fetching: binaries and asset files.
SKIP_EXTENSIONS = (
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".zip", ".gz", ".tar",
    ".rar", ".7z", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".ico", ".bmp",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".css", ".js", ".json", ".xml", ".rss",
    ".exe", ".dmg", ".apk",
)

# Paths that are never a company's own public content.
SKIP_PATH_PATTERNS = re.compile(
    r"/(wp-admin|wp-login|wp-json|admin|login|signin|sign-in|signup|sign-up|register"
    r"|logout|cart|checkout|basket|account|cdn-cgi|feed)(/|$)",
    re.IGNORECASE,
)

SOCIAL_HOSTS = frozenset(
    {
        "facebook.com", "twitter.com", "x.com", "linkedin.com", "instagram.com",
        "youtube.com", "tiktok.com", "pinterest.com", "reddit.com", "github.com",
        "medium.com", "t.me", "wa.me", "goo.gl", "maps.google.com",
    }
)


@dataclass(order=True)
class Candidate:
    """A discovered link worth considering, ordered by crawl priority."""

    priority: int
    depth: int
    url: str = field(compare=False)
    page_type: str = field(compare=False)
    # True when the URL was guessed rather than found. A speculative URL that
    # turns out not to exist is an expected outcome, not a failed fetch, so it
    # is not recorded on the scan or counted against the page budget.
    speculative: bool = field(compare=False, default=False)


# Well-known paths for the page types the specification names. Used only when
# link discovery did not already find that type -- some sites navigate with
# JavaScript (`<button>Careers</button>` with a click handler and no anchor),
# which leaves their careers page public and indexed but unreachable to any
# crawler that only follows `<a href>`.
PROBE_PATHS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (PageType.CAREERS, ("/careers", "/career", "/join-us", "/work-with-us")),
    (PageType.JOBS, ("/jobs", "/vacancies", "/opportunities")),
    (PageType.CONTACT, ("/contact", "/contact-us")),
    (PageType.TEAM, ("/team", "/our-team")),
    (PageType.ABOUT, ("/about", "/about-us")),
)


def probe_candidates(root_url: str, *, already_found: set[str]) -> list[Candidate]:
    """Guessed URLs for the page types link discovery missed.

    Only types absent from ``already_found`` are probed, so a site that links
    its careers page normally costs no extra requests at all.
    """
    origin = root_url.rstrip("/")
    candidates: list[Candidate] = []

    for page_type, paths in PROBE_PATHS:
        if page_type in already_found:
            continue
        for path in paths:
            candidates.append(
                Candidate(
                    priority=TYPE_PRIORITY.get(page_type, TYPE_PRIORITY[PageType.OTHER]),
                    depth=1,
                    url=f"{origin}{path}",
                    page_type=page_type,
                    speculative=True,
                )
            )

    return sorted(candidates)


def registrable_host(url: str) -> str:
    """Returns the hostname without a leading ``www.``."""
    host = (urlsplit(url).hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def is_same_site(candidate_url: str, root_url: str) -> bool:
    """True when the candidate belongs to the company's own site.

    Subdomains count (``careers.example.com`` is very often where the jobs
    live), but unrelated hosts and social networks do not.
    """
    candidate = registrable_host(candidate_url)
    root = registrable_host(root_url)
    if not candidate or not root:
        return False
    if candidate in SOCIAL_HOSTS:
        return False
    return candidate == root or candidate.endswith(f".{root}") or root.endswith(f".{candidate}")


def classify_page_type(url: str, link_text: str = "") -> str:
    """Categorises a page from its URL path and the text that linked to it."""
    path = urlsplit(url).path.lower()
    if path in ("", "/", "/index.html", "/index.htm", "/home"):
        return PageType.HOME

    haystack = f"{path} {link_text.lower()}"
    for page_type, keywords in PAGE_TYPE_KEYWORDS:
        for keyword in keywords:
            # Word-ish boundary so "jobs" does not match "jobsworth" and
            # "about" does not match "aboutique".
            if re.search(rf"(?<![a-z]){re.escape(keyword)}(?![a-z])", haystack):
                return page_type
    return PageType.OTHER


def _should_skip(url: str) -> bool:
    parts = urlsplit(url)
    path = parts.path.lower()
    if path.endswith(SKIP_EXTENSIONS):
        return True
    return bool(SKIP_PATH_PATTERNS.search(path))


def normalize_link(href: str, base_url: str) -> str | None:
    """Resolves a raw href to an absolute, fragment-free http(s) URL."""
    href = (href or "").strip()
    if not href or href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return None

    absolute, _ = urldefrag(urljoin(base_url, href))
    parts = urlsplit(absolute)
    if parts.scheme.lower() not in ("http", "https"):
        return None
    if not parts.hostname:
        return None

    # Treat "/careers" and "/careers/" as one page.
    if parts.path.endswith("/") and len(parts.path) > 1:
        absolute = absolute.replace(parts.path, parts.path.rstrip("/"), 1)
    return absolute


def discover_links(html: str, base_url: str, root_url: str, *, depth: int) -> list[Candidate]:
    """Extracts same-site candidate pages from one fetched document.

    Returns them sorted by priority, de-duplicated within this document.
    """
    soup = BeautifulSoup(html, "lxml")
    seen: dict[str, Candidate] = {}

    for anchor in soup.find_all("a", href=True):
        url = normalize_link(anchor.get("href"), base_url)
        if not url or _should_skip(url) or not is_same_site(url, root_url):
            continue

        page_type = classify_page_type(url, anchor.get_text(" ", strip=True)[:120])
        candidate = Candidate(
            priority=TYPE_PRIORITY.get(page_type, TYPE_PRIORITY[PageType.OTHER]),
            depth=depth,
            url=url,
            page_type=page_type,
        )
        # Keep the best classification if the same URL is linked twice.
        existing = seen.get(url)
        if existing is None or candidate.priority < existing.priority:
            seen[url] = candidate

    return sorted(seen.values())


def extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    if soup.title and soup.title.string:
        return soup.title.string.strip()[:500]
    return ""
