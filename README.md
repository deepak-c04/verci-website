# Aurafy website preview

This is a self-contained, dependency-free static site. The public build is deployed by the GitHub Pages workflow in `.github/workflows/pages.yml`; app ZIPs are attached to the `aurafy-preview-2026-11-19` GitHub release and are not stored in the Pages repository. The workflow validates page structure and checks each linked release asset before publishing.

## Preview locally

From the project root, run:

```sh
python3 -m http.server 8080
```

Then open `http://localhost:8080/website/`. On this local path, download buttons point to the ZIPs in the workspace `dist/` directory. On the published Pages URL, the site links to the GitHub prerelease assets.

## Published layout

The site expects the published files to preserve this relationship:

```text
verci-website/       # public repository; contains only this website and its Pages workflow
  index.html
  styles.css
  site.js
  privacy.html
  aurafy-mark.svg
  robots.txt
  sitemap.xml
  .github/workflows/pages.yml
Aurafy early preview # GitHub prerelease assets: five app ZIPs and SHA256SUMS.txt
```

The large ZIPs stay in GitHub Releases so the Pages artifact remains small. The repository contains no desktop app source, user attachments, or unpacked build directories. The app packages are early previews: the Mac app is not notarized and the Windows packages are unsigned.

Before calling Aurafy a production release, replace the preview downloads with signed/notarized releases, verify installation on target Mac and Windows devices, and update the download links and support notes. The website itself makes no analytics, cookie, or third-party font requests. Browsers contact GitHub only when a visitor chooses a release download.
