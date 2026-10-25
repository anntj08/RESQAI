"""Acquire KSDMA landslide-year pages' documents and the GFLD supplementary tables.

KSDMA (Kerala State Disaster Management Authority) publishes per-year landslide
event reports, which is the most likely home for 2019 (Puthumala), 2021 and 2024
event records that GSI's public report index does not cover.
"""
import pathlib
import re
import sys

import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

H = {"User-Agent": "Mozilla/5.0 (compatible; RESQAI-research/1.0; academic use)"}
BASE = "https://sdma.kerala.gov.in"

PAGES = ["/landslides-2018/", "/landslides-2019/", "/landslides-2021/",
         "/landslides-2024/", "/reports-landslides-2024/", "/disaster-reports/",
         "/landslide-early-warning/", "/land-slide/"]

found = {}
for p in PAGES:
    try:
        r = requests.get(BASE + p, headers=H, timeout=60)
    except Exception as e:
        print(f"{p:34s} ERR {type(e).__name__}")
        continue
    links = re.findall(r'href="([^"]+\.(?:pdf|zip|xlsx|docx|doc))"', r.text, re.I)
    print(f"{p:34s} {r.status_code}  documents={len(links)}")
    for l in links:
        if l.startswith("/"):
            l = BASE + l
        found.setdefault(l, set()).add(p)

print(f"\ndistinct document URLs: {len(found)}")
OUT = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\ksdma")
OUT.mkdir(parents=True, exist_ok=True)

manifest = pathlib.Path(r"C:\Major\data\interim\ksdma_document_urls.csv")
with open(manifest, "w", encoding="utf-8", newline="") as f:
    f.write("url,found_on_pages\n")
    for u, pages in sorted(found.items()):
        f.write(f'"{u}","{";".join(sorted(pages))}"\n')
print("wrote", manifest)

# print the list so the following step can choose which to fetch
for u, pages in sorted(found.items()):
    print(f"  {u[:150]:150s}  <- {','.join(sorted(pages))}")
