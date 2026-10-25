"""Fetch the open-access full text of two 2025 event papers via the PMC OA service
and pull their per-event tables.

PMC12749052  Sreekumar et al. 2025, Sci Rep — Table 1 lists recent Kerala events
             with locality, date and DMS coordinates (Mundakkai 2024, Puthumala
             2019, Kavalappara/Pathar 2019, Irumbachola 2021, Kannappankundu 2018).
PMC12290006  Ramesh et al. 2025, Sci Rep — Mundakkai-Chooralmala initiation
             timing, runout and peak rainfall.

The XML is used rather than the HTML because the HTML renders the tables with
scripts and loses cell text.
"""
import pathlib
import re
import xml.etree.ElementTree as ET

import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
OUT = pathlib.Path(r"C:\Major\data\raw\literature_events")
OUT.mkdir(parents=True, exist_ok=True)

for pmc in ("PMC12749052", "PMC12290006"):
    url = ("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
           f"?db=pmc&id={pmc.replace('PMC', '')}&rettype=xml")
    r = requests.get(url, headers=H, timeout=120)
    print(f"{pmc}: {r.status_code}  {len(r.content)} bytes")
    if r.ok and b"<article" in r.content:
        (OUT / f"{pmc}.xml").write_bytes(r.content)

print("\n--- tables found ---")
for pmc in ("PMC12749052", "PMC12290006"):
    p = OUT / f"{pmc}.xml"
    if not p.exists():
        print(pmc, "no xml")
        continue
    txt = p.read_text(encoding="utf-8", errors="replace")
    tables = re.findall(r"<table-wrap\b.*?</table-wrap>", txt, re.S)
    print(f"\n===== {pmc}: {len(tables)} table-wrap elements")
    for i, t in enumerate(tables):
        label = re.search(r"<label>(.*?)</label>", t, re.S)
        cap = re.search(r"<caption>(.*?)</caption>", t, re.S)
        cap_t = re.sub(r"<[^>]+>", " ", cap.group(1)) if cap else ""
        cap_t = re.sub(r"\s+", " ", cap_t).strip()
        nrows = len(re.findall(r"<tr\b", t))
        print(f"  [{i}] {label.group(1) if label else '?'}  rows={nrows}  {cap_t[:130]}")
