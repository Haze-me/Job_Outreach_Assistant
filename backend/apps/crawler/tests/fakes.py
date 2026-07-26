"""A stand-in for ``SafeHttpClient`` so scans can be tested without a network.

The real client is covered separately by the SSRF and robots unit tests. What
these fakes exercise is the orchestration around it: which pages get visited,
in what order, how many, and what is stored.
"""

from __future__ import annotations

from apps.crawler.services.http import FetchError, FetchResult


class FakeRobots:
    def __init__(self, disallowed: set[str] | None = None) -> None:
        self.disallowed = disallowed or set()

    def is_allowed(self, url: str) -> bool:
        return url not in self.disallowed


class FakeHttpClient:
    """Serves a fixed ``{url: html}`` map and records what was requested."""

    def __init__(
        self,
        pages: dict[str, str],
        *,
        disallowed: set[str] | None = None,
        failing: set[str] | None = None,
        redirects: dict[str, str] | None = None,
        text_resources: dict[str, str] | None = None,
    ) -> None:
        self.pages = pages
        self.failing = failing or set()
        self.redirects = redirects or {}
        # robots.txt and sitemap.xml live here. Absent by default, which is
        # the common real-world case.
        self.text_resources = text_resources or {}
        self.requested: list[str] = []
        self.text_requested: list[str] = []
        self.robots = FakeRobots(disallowed)

    def get_text(self, url: str) -> str | None:
        """Non-HTML fetches (robots.txt, sitemaps). None when absent."""
        self.text_requested.append(url)
        return self.text_resources.get(url)

    def __enter__(self) -> FakeHttpClient:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def close(self) -> None:
        pass

    def get_html(self, url: str) -> FetchResult:
        self.requested.append(url)
        if url in self.failing:
            raise FetchError(f"Simulated failure for {url}")

        final_url = self.redirects.get(url, url)
        try:
            html = self.pages[final_url]
        except KeyError as exc:
            raise FetchError(f"HTTP 404 for {final_url}") from exc

        return FetchResult(
            url=final_url,
            status_code=200,
            html=html,
            content_type="text/html; charset=utf-8",
        )


def install(monkeypatch, client: FakeHttpClient) -> FakeHttpClient:
    """Points the scanner at ``client`` instead of the real HTTP client."""
    from apps.crawler.services import scanner

    monkeypatch.setattr(scanner, "SafeHttpClient", lambda **kwargs: client)
    return client
