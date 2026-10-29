"""Targeted extraction of the NDMA 'Landslide (425 MB)' page: context around
'425' and the full href list, to identify the download.

RUN-2026-10-29-09 evidence step (catalogue-level only).
"""
from __future__ import annotations

import re
import sys

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
r = requests.get("https://ndma.gov.in/en/landslide-425-mb", headers=H, timeout=60)
text = r.text
body = re.sub(r"<script.*?</script>", "", text, flags=re.S)
body = re.sub(r"<[^>]+>", " ", body)
body = re.sub(r"\s+", " ", body).strip()

print("page:", r.status_code, len(r.content))
for m in re.finditer(r"425", body):
    print("\n425-ctx:", body[max(0, m.start() - 350):m.start() + 350])

print("\n--- all hrefs (dedup, first 45) ---")
seen = set()
for h, lab in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', text, re.S | re.I):
    lab = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lab)).strip()
    if h not in seen:
        seen.add(h)
        print(f"  {h[:130]}  |  {lab[:80]}")
    if len(seen) >= 45:
        break

print("\n--- title ---")
t = re.search(r"<title>([^<]*)</title>", text, re.I)
print(t.group(1) if t else "?")
