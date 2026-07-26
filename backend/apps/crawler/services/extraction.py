"""Email address extraction from fetched HTML.

Four sources are read, in descending order of confidence:

1. ``mailto:`` links -- unambiguous.
2. Cloudflare-obfuscated addresses. Cloudflare's "Email Address Obfuscation"
   feature is on by default for a great many sites: it replaces the address in
   the markup with the literal text "[email protected]" and hides the real
   value, XOR-encoded, in a ``data-cfemail`` attribute. Without decoding it,
   those pages appear to contain no addresses at all.
3. Plain text on the page.
4. Deliberately obfuscated text such as ``careers [at] example [dot] com``,
   written that way specifically to defeat scrapers.

Script and style blocks are removed first -- they are full of strings that look
like addresses (analytics keys, source-map comments, minified identifiers) and
produce nothing but noise.
"""

from __future__ import annotations

import re
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

# Conservative on purpose: no leading dot, no consecutive dots, and a TLD of at
# least two letters. Over-matching creates junk contacts a user has to clean up.
EMAIL_PATTERN = re.compile(
    r"(?<![A-Za-z0-9._%+\-])"
    r"([A-Za-z0-9_%+\-]+(?:\.[A-Za-z0-9_%+\-]+)*"
    r"@"
    r"(?:[A-Za-z0-9](?:[A-Za-z0-9\-]*[A-Za-z0-9])?\.)+[A-Za-z]{2,})"
    r"(?![A-Za-z0-9\-])"
)

# Domains that are never a real recruitment contact.
BLOCKED_DOMAIN_SUFFIXES = (
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".css", ".js", ".json",
    ".php", ".html", ".htm", ".webp2x",
)
BLOCKED_DOMAINS = frozenset(
    {
        "sentry.io", "wixpress.com", "example.com", "example.org", "example.net",
        "domain.com", "yourdomain.com", "email.com", "test.com",
    }
)
# Placeholder local parts that appear in template markup.
BLOCKED_LOCAL_PARTS = frozenset(
    {"email", "your-email", "youremail", "name", "yourname", "user", "username", "someone"}
)

# Image sprites such as "logo@2x.png" survive the regex; so do version strings.
ASSET_LOCAL_PART = re.compile(r"^\d+x$|^\d+$")

# ---------------------------------------------------------------------------
# Deliberate text obfuscation
# ---------------------------------------------------------------------------
# Only *delimited* separators are accepted -- "[at]", "(at)", "-at-" and so on.
# A bare " at " is deliberately NOT supported: "contact us at example.com" is
# ordinary English, and treating it as an address would invent
# "us@example.com". Precision matters more than recall here, because the cost
# of a false positive is a junk contact the user has to notice and clean up.
_AT = r"(?:\[\s*(?:at|@)\s*\]|\(\s*(?:at|@)\s*\)|\{\s*(?:at|@)\s*\}|\s-at-\s)"
_DOT = r"(?:\[\s*(?:dot|\.)\s*\]|\(\s*(?:dot|\.)\s*\)|\{\s*(?:dot|\.)\s*\}|\s-dot-\s|\.)"

OBFUSCATED_PATTERN = re.compile(
    rf"([A-Za-z0-9._%+\-]+)\s*{_AT}\s*"
    rf"([A-Za-z0-9\-]+(?:\s*{_DOT}\s*[A-Za-z0-9\-]+)+)",
    re.IGNORECASE,
)
_DOT_SEPARATOR = re.compile(rf"\s*{_DOT}\s*", re.IGNORECASE)


def decode_cfemail(encoded: str) -> str | None:
    """Decodes a Cloudflare ``data-cfemail`` value.

    The scheme is simple: the first byte of the hex string is an XOR key, and
    every following byte is a character of the address XOR-ed with it.
    """
    try:
        data = bytes.fromhex(encoded.strip())
    except ValueError:
        return None
    if len(data) < 2:
        return None

    key = data[0]
    try:
        return "".join(chr(byte ^ key) for byte in data[1:])
    except ValueError:  # pragma: no cover - defensive
        return None


def _from_cloudflare(soup: BeautifulSoup) -> list[str]:
    """Recovers addresses Cloudflare replaced with '[email protected]'."""
    found: list[str] = []

    for element in soup.select("[data-cfemail]"):
        decoded = decode_cfemail(element.get("data-cfemail", ""))
        if decoded:
            found.append(decoded)

    # The same encoding also appears in the href of protected mailto links.
    for anchor in soup.select('a[href*="/cdn-cgi/l/email-protection#"]'):
        _, _, encoded = anchor["href"].partition("#")
        decoded = decode_cfemail(encoded)
        if decoded:
            found.append(decoded)

    return found


def _from_obfuscated_text(text: str) -> list[str]:
    """Reassembles addresses written as 'careers [at] example [dot] com'."""
    found: list[str] = []

    for local, domain in OBFUSCATED_PATTERN.findall(text):
        rebuilt_domain = _DOT_SEPARATOR.sub(".", domain).strip(".")
        if not rebuilt_domain:
            continue
        found.append(f"{local}@{rebuilt_domain}")

    return found


def _is_plausible(email: str) -> bool:
    """Filters out matches that are syntactically valid but obviously not contacts."""
    try:
        validate_email(email)
    except ValidationError:
        return False

    local, _, domain = email.rpartition("@")
    if not local or not domain:
        return False
    if domain in BLOCKED_DOMAINS or domain.endswith(BLOCKED_DOMAIN_SUFFIXES):
        return False
    if local in BLOCKED_LOCAL_PARTS or ASSET_LOCAL_PART.match(local):
        return False
    return len(email) <= 254


def _from_mailto_links(soup: BeautifulSoup) -> list[str]:
    found: list[str] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href.lower().startswith("mailto:"):
            continue
        # mailto:a@b.com?subject=Hi  ->  a@b.com  (and percent-decoded)
        target = unquote(urlsplit(href).path or href[7:])
        for part in target.split(","):
            candidate = part.split("?")[0].strip()
            if candidate:
                found.append(candidate)
    return found


def extract_emails(html: str) -> list[str]:
    """Returns unique, lower-cased, plausible email addresses found in ``html``.

    Order is stable: ``mailto:`` links first (they are the strongest signal),
    then addresses found in the visible text.
    """
    soup = BeautifulSoup(html, "lxml")

    # Decode Cloudflare's obfuscation before stripping scripts: the encoded
    # value lives on ordinary elements, but the placeholder text it leaves
    # behind ("[email protected]") is worthless without it.
    candidates = _from_cloudflare(soup)

    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()

    candidates.extend(_from_mailto_links(soup))

    text = soup.get_text(" ", strip=True)
    candidates.extend(EMAIL_PATTERN.findall(text))
    candidates.extend(_from_obfuscated_text(text))

    unique: list[str] = []
    seen: set[str] = set()
    for raw in candidates:
        email = raw.strip().strip(".,;:").lower()
        if email in seen or not _is_plausible(email):
            continue
        seen.add(email)
        unique.append(email)

    return unique
