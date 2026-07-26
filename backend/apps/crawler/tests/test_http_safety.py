"""SSRF protection and robots.txt handling."""

import socket

import pytest

from apps.crawler.services.http import RobotsPolicy, UnsafeUrlError, assert_safe_url


def _fake_getaddrinfo(*addresses: str):
    """Builds a getaddrinfo replacement returning fixed addresses."""

    def _resolver(host, port, *args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", (address, 0)) for address in addresses]

    return _resolver


class TestSchemeAndShape:
    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com",
            "file:///etc/passwd",
            "gopher://example.com",
            "javascript:alert(1)",
        ],
    )
    def test_rejects_non_http_schemes(self, url):
        with pytest.raises(UnsafeUrlError):
            assert_safe_url(url, allow_private=False)

    def test_rejects_url_without_a_host(self):
        with pytest.raises(UnsafeUrlError):
            assert_safe_url("http:///nohost", allow_private=False)


class TestLiteralAddresses:
    @pytest.mark.parametrize(
        "url",
        [
            "http://127.0.0.1/",
            "http://127.0.0.1:8000/admin",
            "http://0.0.0.0/",
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://172.16.0.1/",
            # The AWS/GCP instance-metadata endpoint -- the classic SSRF target.
            "http://169.254.169.254/latest/meta-data/",
            "http://[::1]/",
            "http://[fe80::1]/",
        ],
    )
    def test_rejects_non_public_literals(self, url):
        with pytest.raises(UnsafeUrlError):
            assert_safe_url(url, allow_private=False)

    def test_allows_a_public_literal(self):
        assert assert_safe_url("http://93.184.216.34/", allow_private=False)


class TestHostnameResolution:
    def test_rejects_a_hostname_resolving_to_loopback(self, monkeypatch):
        monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo("127.0.0.1"))

        with pytest.raises(UnsafeUrlError, match="non-public"):
            assert_safe_url("https://evil.example.com/", allow_private=False)

    def test_rejects_when_any_resolved_address_is_private(self, monkeypatch):
        # A host can return a public and a private record; the connection could
        # use either, so one bad address is enough to refuse.
        monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34", "10.0.0.9"))

        with pytest.raises(UnsafeUrlError):
            assert_safe_url("https://mixed.example.com/", allow_private=False)

    def test_allows_a_fully_public_hostname(self, monkeypatch):
        monkeypatch.setattr(socket, "getaddrinfo", _fake_getaddrinfo("93.184.216.34"))

        assert assert_safe_url("https://example.com/", allow_private=False)

    def test_rejects_an_unresolvable_hostname(self, monkeypatch):
        def _boom(*args, **kwargs):
            raise socket.gaierror("nope")

        monkeypatch.setattr(socket, "getaddrinfo", _boom)

        with pytest.raises(UnsafeUrlError, match="resolve"):
            assert_safe_url("https://nx.example.com/", allow_private=False)

    def test_escape_hatch_skips_all_checks(self):
        # Used only by the test suite; the setting defaults to False.
        assert assert_safe_url("http://127.0.0.1:8000/", allow_private=True)


class TestRobotsPolicy:
    def test_disallowed_path_is_blocked(self):
        robots = "User-agent: *\nDisallow: /private\n"
        policy = RobotsPolicy(user_agent="TestBot", fetch=lambda url: robots)

        assert policy.is_allowed("https://example.com/careers") is True
        assert policy.is_allowed("https://example.com/private/data") is False

    def test_missing_robots_txt_allows_everything(self):
        policy = RobotsPolicy(user_agent="TestBot", fetch=lambda url: None)

        assert policy.is_allowed("https://example.com/anything") is True

    def test_fetch_failure_allows_everything(self):
        def _boom(url):
            raise OSError("connection reset")

        policy = RobotsPolicy(user_agent="TestBot", fetch=_boom)

        assert policy.is_allowed("https://example.com/anything") is True

    def test_disabled_policy_skips_fetching(self):
        calls = []

        def _fetch(url):
            calls.append(url)
            return "User-agent: *\nDisallow: /\n"

        policy = RobotsPolicy(user_agent="TestBot", fetch=_fetch, enabled=False)

        assert policy.is_allowed("https://example.com/private") is True
        assert calls == []

    def test_robots_txt_is_fetched_once_per_host(self):
        calls = []

        def _fetch(url):
            calls.append(url)
            return "User-agent: *\nDisallow: /private\n"

        policy = RobotsPolicy(user_agent="TestBot", fetch=_fetch)
        policy.is_allowed("https://example.com/a")
        policy.is_allowed("https://example.com/b")
        policy.is_allowed("https://other.example.com/c")

        assert len(calls) == 2

    def test_blanket_disallow_blocks_the_site(self):
        policy = RobotsPolicy(
            user_agent="TestBot", fetch=lambda url: "User-agent: *\nDisallow: /\n"
        )

        assert policy.is_allowed("https://example.com/") is False
