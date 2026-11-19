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
if "Optional live Auto Sync" not in index or "Manual Offset &amp; Pace" not in index:
    fail("index.html: platform-specific Auto Sync availability copy is missing")
if "Live Auto Sync is not available yet" not in site_js:
    fail("site.js: Windows Auto Sync availability copy is missing")

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
