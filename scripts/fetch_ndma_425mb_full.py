"""Full href list + content body for the NDMA 'Landslide (42.5 MB)' page.

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

print("page:", r.status_code, len(r.content))
print("--- file-like hrefs ---")
seen = set()
for h, lab in re.findall(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', text, re.S | re.I):
    lab = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", lab)).strip()
    if h in seen:
        continue
    seen.add(h)
    if re.search(r"/sites/default/files/|\.pdf|\.zip|\.rar|\.xlsx|\.gpkg|drive\.|docs\.|bit\.ly",
                 h, re.I) and "Recruitment" not in h and "COMPENDIUM" not in h \
            and "SFDRR" not in h:
        print(f"  {h[:140]}  |  {lab[:80]}")

body = re.sub(r"<script.*?</script>", "", text, flags=re.S)
body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
body = re.sub(r"<[^>]+>", " ", body)
body = re.sub(r"\s+", " ", body).strip()
m = re.search(r"Hospital Safety(.{0,2500})", body)
print("\n--- body after nav ---")
print((m.group(1) if m else body[-2500:])[:2500])
