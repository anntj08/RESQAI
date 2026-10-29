"""Fetch the two NDMA landslide sub-pages and dump their body text + download
hrefs, to identify what the '(425 MB)' landslide item is.

RUN-2026-10-29-09 evidence step (catalogue-level only).
"""
from __future__ import annotations

import re
import sys

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}

for key, url in [("landslide-0", "https://ndma.gov.in/en/landslide-0"),
                 ("landslide-425mb", "https://ndma.gov.in/en/landslide-425-mb")]:
    r = requests.get(url, headers=H, timeout=60)
    body = re.sub(r"<script.*?</script>", "", r.text, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<[^>]+>", " ", body)
    body = re.sub(r"\s+", " ", body).strip()
    print("===", key, r.status_code, len(r.content), r.url)
    m = re.search(r"Main navigation(.{0,1400})", body)
    print((m.group(1) if m else body)[:1400])
    print("download hrefs:",
          re.findall(r'href="([^"]+(?:pdf|zip|rar|7z)[^"]*)"', r.text)[:10])
    print()
