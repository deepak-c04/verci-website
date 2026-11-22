#!/usr/bin/env python3
"""Validate the static Pages payload and its published preview downloads."""

from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[2]


class PageAudit(HTMLParser):
    def __init__(self, path: Path) -> None:
        super().__init__(convert_charrefs=True)
        self.path = path
        self.ids: list[str] = []
        self.references: list[str] = []
        self.local_links: list[str] = []
        self.download_names: list[str] = []
        self.inline_code: list[str] = []
        self.csp_policies: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "meta" and (values.get("http-equiv") or "").lower() == "content-security-policy":
            self.csp_policies.append(values.get("content") or "")
        if any(attribute.lower() == "style" for attribute, _ in attrs):
            self.inline_code.append("inline style attribute")
        if any(attribute.lower().startswith("on") and len(attribute) > 2 for attribute, _ in attrs):
            self.inline_code.append("inline event handler")
        if values.get("id"):
            self.ids.append(values["id"] or "")
        for attribute in ("aria-labelledby", "aria-controls", "aria-describedby"):
            self.references.extend((values.get(attribute) or "").split())
        if tag in {"a", "link", "script", "img"}:
            destination = values.get("href") or values.get("src")
            if destination:
                self.local_links.append(destination)
                if tag == "a" and destination.startswith("../dist/"):
                    self.download_names.append(Path(destination).name)
        if tag == "script" and not values.get("src"):
            self.inline_code.append("inline script")
        if tag == "style":
            self.inline_code.append("inline style")


def fail(message: str) -> None:
    raise SystemExit(message)


def audit_page(path: Path) -> PageAudit:
    filename = path.name
    audit = PageAudit(path)
    audit.feed(path.read_text(encoding="utf-8"))
    duplicates = sorted({item for item in audit.ids if audit.ids.count(item) > 1})
    if duplicates:
        fail(f"{filename}: duplicate IDs: {', '.join(duplicates)}")
    missing_references = sorted(set(audit.references) - set(audit.ids))
    if missing_references:
        fail(f"{filename}: missing ARIA targets: {', '.join(missing_references)}")
    if audit.inline_code:
        fail(f"{filename}: inline code is blocked by the site's CSP")
    expected_csp = {
        "default-src": {"'self'"},
        "base-uri": {"'self'"},
        "object-src": {"'none'"},
        "script-src": {"'self'"},
        "style-src": {"'self'"},
        "img-src": {"'self'", "data:"},
        "font-src": {"'self'"},
        "connect-src": {"'self'"},
        "form-action": {"'none'"},
    }
    actual_csp: dict[str, set[str]] = {}
    if len(audit.csp_policies) == 1:
        for directive in audit.csp_policies[0].split(";"):
            parts = directive.strip().lower().split()
            if not parts:
                continue
            if parts[0] in actual_csp:
                fail(f"{filename}: duplicate CSP directive {parts[0]}")
            actual_csp[parts[0]] = set(parts[1:])
    if any(actual_csp.get(name) != sources for name, sources in expected_csp.items()):
        fail(f"{filename}: missing or weakened Content-Security-Policy")

    for destination in audit.local_links:
        if destination.startswith(("https://", "http://", "mailto:", "data:")):
            continue
        if destination.startswith("../dist/"):
            continue
        local_path, _, fragment = destination.partition("#")
        if local_path and not (path.parent / local_path).resolve().is_file():
            fail(f"{filename}: missing local destination {destination}")
    return audit


audits = {path.name: audit_page(path) for path in sorted(ROOT.glob("*.html"))}
audits_by_path = {(ROOT / name).resolve(): audit for name, audit in audits.items()}
for filename, audit in audits.items():
    for destination in audit.local_links:
        if destination.startswith(("https://", "http://", "mailto:", "data:", "../dist/")):
            continue
        local_path, _, fragment = destination.partition("#")
        if not fragment:
            continue
        target = (ROOT / local_path).resolve() if local_path else (ROOT / filename).resolve()
        if target.suffix.lower() == ".html":
            target_audit = audits_by_path.get(target)
            if target_audit is None or fragment not in target_audit.ids:
                fail(f"{filename}: missing fragment target {destination}")
index = (ROOT / "index.html").read_text(encoding="utf-8")
site_js = (ROOT / "site.js").read_text(encoding="utf-8")
sync_card_match = re.search(r'<article class="feature-card feature-card-sync"[^>]*>(.*?)</article>', index, re.S)
if not sync_card_match:
    fail("index.html: Auto Sync feature card is missing")
sync_card = sync_card_match.group(1)
if "Optional live Auto Sync" not in sync_card or "Manual timing in download" not in sync_card:
    fail("index.html: platform-specific Auto Sync availability copy is missing")
windows_badge = re.search(r'<div><span>WINDOWS</span><p>([^<]*)</p></div>', sync_card)
if not windows_badge or "not included" not in windows_badge.group(1).lower():
    fail("index.html: Windows Auto Sync badge must disclose that it is not included")
if "Live Auto Sync is in development and not in the current download" not in site_js:
    fail("site.js: Windows Auto Sync availability copy is missing")
if "Compatibility in preview" not in index or "Laptop check: passed" in index:
    fail("index.html: compatibility headline overstates physical-device verification")
if "On Mac · private by default" not in sync_card or "Mac: Screen &amp; System Audio Recording" not in sync_card:
    fail("index.html: Mac-only Auto Sync privacy and permission copy is not labeled")
if "Windows source prototype needs build 20348 or later" not in sync_card:
    fail("index.html: Windows Auto Sync source build requirement is missing from the feature card")

windows_download_match = re.search(
    r'<article class="download-card download-card-win"[^>]*>(.*?)</article>', index, re.S)
windows10_download_match = re.search(
    r'<details class="download-legacy"[^>]*>(.*?)</details>', index, re.S)
if not windows_download_match or \
        "Auto Sync is not included in this Windows download." not in windows_download_match.group(1):
    fail("index.html: Windows Store and ZIP path must disclose that Auto Sync is not included")
if not windows10_download_match or \
        "Auto Sync is not included in this Windows 10 download." not in windows10_download_match.group(1):
    fail("index.html: Windows 10 Enterprise or LTSC path must disclose that Auto Sync is not included")

privacy = (ROOT / "privacy.html").read_text(encoding="utf-8")
windows_privacy_match = re.search(
    r'<h2>Windows Auto Sync is in development</h2>\s*<p>(.*?)</p>', privacy, re.S)
if not windows_privacy_match:
    fail("privacy.html: Windows Auto Sync preview and audio-capture boundaries are missing")
windows_privacy = windows_privacy_match.group(1)
if "current Windows download does not include live Auto Sync" not in windows_privacy or \
        "excludes the microphone and system-wide audio mix" not in windows_privacy or \
        "Windows build 20348 or later" not in windows_privacy or "child processes" not in windows_privacy:
    fail("privacy.html: Windows Auto Sync preview and audio-capture boundaries are missing")

styles = (ROOT / "styles.css").read_text(encoding="utf-8")
for selector, minimum in ((".download-foot", 12), (".download-copy", 12),
                          (".download-links a", 12), (".download-links small", 12),
                          (".download-disclaimer p", 12), (".download-disclaimer a", 12),
                          (".privacy-copy > p:not(.eyebrow)", 13),
                          (".privacy-content p, .privacy-content li", 13)):
    rules = re.findall(re.escape(selector) + r"\s*\{([^}]*)\}", styles)
    sizes = [float(match.group(1)) for rule in rules if (match := re.search(r"font-size:\s*([0-9.]+)px", rule))]
    if not sizes or min(sizes) < minimum:
        fail(f"styles.css: essential disclosure text for {selector} is below {minimum}px")

release_match = re.search(r'const releaseBase = "([^"]+)";', site_js)
if not release_match:
    fail("site.js: public release base URL is missing")
release_base = release_match.group(1)
download_names = sorted(set(audits["index.html"].download_names))
if not download_names:
    fail("index.html: no release downloads found to validate")

for name in download_names:
    url = release_base + quote(name)
    request = Request(url, method="HEAD", headers={"User-Agent": "Aurafy-Pages-validation"})
    try:
        with urlopen(request, timeout=30) as response:
            if response.status >= 400:
                fail(f"Release asset returned HTTP {response.status}: {name}")
    except (HTTPError, URLError, TimeoutError) as error:
        fail(f"Could not verify release asset {name}: {error}")

print(f"Validated {len(audits)} pages, {len(download_names)} release assets, IDs, ARIA references, links, CSP, and Auto Sync platform copy.")
