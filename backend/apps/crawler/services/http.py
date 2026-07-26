"""Safe HTTP fetching for the crawler.

The crawler follows URLs supplied by users, which makes it a server-side
request forgery (SSRF) vector unless every request is checked. The rules
enforced here:

* only ``http`` and ``https``
* the hostname must resolve exclusively to public IP addresses -- no loopback,
  private, link-local, multicast, or otherwise reserved ranges
* redirects are followed manually so each hop is re-validated (a public URL
  that 302s to ``http://169.254.169.254/`` is the classic cloud-metadata
  attack)
* responses are capped in size and time, and only HTML is read

Known limitation: there is a small window between resolving a hostname and
connecting to it in which DNS could change (a "DNS rebinding" attack). Closing
it entirely requires pinning the checked IP into the connection, which httpx
does not expose. The remaining exposure is a single fetch of an internal URL
whose body is never returned to the user -- only extracted email addresses are.
"""

from __future__ import annotations

import ipaddress
import logging
import socket
import time
from dataclasses import dataclass
from urllib import robotparser
from urllib.parse import urlsplit

import httpx
from django.conf import settings

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = frozenset({"http", "https"})
HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")


class UnsafeUrlError(Exception):
    """Raised when a URL must not be requested."""


class FetchError(Exception):
    """Raised when a page could not be retrieved."""


@dataclass(frozen=True)
class FetchResult:
    url: str
    status_code: int
    html: str
    content_type: str


def _is_public_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    """True only for addresses that can route to the public internet."""
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def assert_safe_url(url: str, *, allow_private: bool | None = None) -> str:
    """Validates a URL for outbound fetching, returning it unchanged.

    Raises ``UnsafeUrlError`` if the scheme is wrong, the host cannot be
    resolved, or *any* address it resolves to is non-public. Checking every
    resolved address matters: a hostname can return one public and one private
    record, and the connection could use either.
    """
    if allow_private is None:
        allow_private = settings.CRAWLER_ALLOW_PRIVATE_NETWORKS

    parts = urlsplit(url)
    if parts.scheme.lower() not in ALLOWED_SCHEMES:
        raise UnsafeUrlError(f"Unsupported URL scheme: {parts.scheme!r}")

    host = parts.hostname
    if not host:
        raise UnsafeUrlError("URL has no hostname.")

    if allow_private:
        # Test-only escape hatch, gated by a setting that defaults to False.
        return url

    # A literal IP in the URL is checked directly; anything else is resolved.
    try:
        literal = ipaddress.ip_address(host)
    except ValueError:
        literal = None

    if literal is not None:
        if not _is_public_ip(literal):
            raise UnsafeUrlError(f"Refusing to fetch a non-public address: {host}")
        return url

    try:
        resolved = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"Could not resolve host: {host}") from exc

    if not resolved:
        raise UnsafeUrlError(f"Could not resolve host: {host}")

    for record in resolved:
        address = ipaddress.ip_address(record[4][0])
        if not _is_public_ip(address):
            raise UnsafeUrlError(f"Host {host} resolves to a non-public address ({address}).")

    return url


class RobotsPolicy:
    """Caches and applies each host's robots.txt for the life of one scan."""

    def __init__(self, *, user_agent: str, fetch, enabled: bool = True) -> None:
        self._user_agent = user_agent
        self._fetch = fetch
        self._enabled = enabled
        self._parsers: dict[str, robotparser.RobotFileParser | None] = {}

    def _parser_for(self, url: str) -> robotparser.RobotFileParser | None:
        parts = urlsplit(url)
        origin = f"{parts.scheme}://{parts.netloc}"
        if origin in self._parsers:
            return self._parsers[origin]

        parser: robotparser.RobotFileParser | None = None
        try:
            body = self._fetch(f"{origin}/robots.txt")
        except Exception:  # noqa: BLE001 - a missing robots.txt is normal
            body = None

        if body:
            parser = robotparser.RobotFileParser()
            parser.parse(body.splitlines())

        self._parsers[origin] = parser
        return parser

    def is_allowed(self, url: str) -> bool:
        """Absent or unreadable robots.txt means crawling is permitted."""
        if not self._enabled:
            return True
        parser = self._parser_for(url)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)


class SafeHttpClient:
    """A deliberately slow, deliberately limited HTTP client.

    One instance is used per scan so connection pooling, the robots.txt cache,
    and the inter-request delay all share the same lifetime.
    """

    def __init__(
        self,
        *,
        user_agent: str | None = None,
        timeout: float | None = None,
        max_bytes: int | None = None,
        max_redirects: int | None = None,
        delay_seconds: float | None = None,
        respect_robots: bool | None = None,
        allow_private: bool | None = None,
    ) -> None:
        self.user_agent = user_agent or settings.CRAWLER_USER_AGENT
        self.timeout = timeout if timeout is not None else settings.CRAWLER_REQUEST_TIMEOUT
        self.max_bytes = max_bytes or settings.CRAWLER_MAX_RESPONSE_BYTES
        self.max_redirects = (
            max_redirects if max_redirects is not None else settings.CRAWLER_MAX_REDIRECTS
        )
        self.delay_seconds = (
            delay_seconds if delay_seconds is not None else settings.CRAWLER_DELAY_SECONDS
        )
        self.allow_private = (
            allow_private
            if allow_private is not None
            else settings.CRAWLER_ALLOW_PRIVATE_NETWORKS
        )
        respect_robots = (
            respect_robots
            if respect_robots is not None
            else settings.CRAWLER_RESPECT_ROBOTS_TXT
        )

        self._client = httpx.Client(
            follow_redirects=False,  # each hop is validated by hand
            timeout=self.timeout,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "en",
            },
        )
        self._last_request_at: float | None = None
        self.robots = RobotsPolicy(
            user_agent=self.user_agent,
            fetch=self._fetch_text,
            enabled=respect_robots,
        )

    # -- lifecycle ---------------------------------------------------------
    def __enter__(self) -> SafeHttpClient:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    # -- internals ---------------------------------------------------------
    def _throttle(self) -> None:
        """Keeps at least ``delay_seconds`` between outbound requests."""
        if self.delay_seconds <= 0:
            return
        if self._last_request_at is not None:
            elapsed = time.monotonic() - self._last_request_at
            remaining = self.delay_seconds - elapsed
            if remaining > 0:
                time.sleep(remaining)
        self._last_request_at = time.monotonic()

    def _read_capped(self, response: httpx.Response) -> str:
        """Reads at most ``max_bytes`` so a huge response cannot exhaust memory."""
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_bytes():
            chunks.append(chunk)
            total += len(chunk)
            if total >= self.max_bytes:
                logger.info("Truncated oversized response from %s", response.url)
                break
        body = b"".join(chunks)[: self.max_bytes]
        encoding = response.encoding or "utf-8"
        return body.decode(encoding, errors="replace")

    def get_text(self, url: str) -> str | None:
        """Public alias for fetching a non-HTML resource (robots.txt, sitemaps)."""
        return self._fetch_text(url)

    def _fetch_text(self, url: str) -> str | None:
        """Fetches a plain-text resource. Returns None on any failure."""
        try:
            assert_safe_url(url, allow_private=self.allow_private)
        except UnsafeUrlError:
            return None
        self._throttle()
        try:
            response = self._client.get(url)
        except httpx.HTTPError:
            return None
        if response.status_code != 200:
            return None
        return response.text

    # -- public API --------------------------------------------------------
    def get_html(self, url: str) -> FetchResult:
        """Fetches an HTML page, following and re-validating redirects.

        Raises ``UnsafeUrlError`` if any hop is not safe to request, and
        ``FetchError`` for transport failures, non-HTML responses, or error
        statuses.
        """
        current = url
        for _ in range(self.max_redirects + 1):
            assert_safe_url(current, allow_private=self.allow_private)
            self._throttle()

            try:
                with self._client.stream("GET", current) as response:
                    if response.is_redirect:
                        location = response.headers.get("location")
                        if not location:
                            raise FetchError(f"Redirect without a Location header: {current}")
                        # Resolve relative redirect targets against the current URL.
                        current = str(httpx.URL(current).join(location))
                        continue

                    if response.status_code >= 400:
                        raise FetchError(f"HTTP {response.status_code} for {current}")

                    content_type = response.headers.get("content-type", "")
                    if not any(kind in content_type for kind in HTML_CONTENT_TYPES):
                        raise FetchError(f"Not an HTML document ({content_type or 'unknown'})")

                    html = self._read_capped(response)
                    return FetchResult(
                        url=str(response.url),
                        status_code=response.status_code,
                        html=html,
                        content_type=content_type,
                    )
            except httpx.HTTPError as exc:
                raise FetchError(f"Could not fetch {current}: {exc}") from exc

        raise FetchError(f"Too many redirects starting at {url}")
