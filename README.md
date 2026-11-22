# Aurafy website preview

This is a self-contained, dependency-free static site. The current public preview is version 2.2.19 build 43 (tag aurafy-preview-2026-11-21-2.2.19-build-43). The GitHub Pages workflow in .github/workflows/pages.yml validates the pages and release assets before deploying; app ZIPs stay attached to the GitHub release.

## Preview locally

From the project root, run:

```sh
python3 -m http.server 8080
```

Then open http://localhost:8080/ from this repository root. In the larger verci workspace, use http://localhost:8080/website/. On the published Pages URL, download buttons link to GitHub prerelease assets.

## Published layout

The site expects the published files to preserve this relationship:

```text
verci-website/       # public repository; contains only this website and its Pages workflow
  index.html
  styles.css
  site.js
  privacy.html
  aurafy-mark.svg
  aurafy.ico
  aurafy-apple-touch-icon.png
  og-image.png
  robots.txt
  sitemap.xml
  .github/workflows/pages.yml
Aurafy early preview # GitHub prerelease assets: five app ZIPs and SHA256SUMS.txt
```

The large ZIPs stay in GitHub Releases so the Pages artifact remains small. The repository contains no desktop app source, user attachments, or unpacked build directories. The app packages are early previews: the Mac app is not notarized and the Windows packages are unsigned.

Before calling Aurafy a production release, replace the preview downloads with signed/notarized releases, verify installation on target Mac and Windows devices, and update the download links and support notes. The website itself makes no analytics, cookie, or third-party font requests. Browsers contact GitHub only when a visitor chooses a release download.
