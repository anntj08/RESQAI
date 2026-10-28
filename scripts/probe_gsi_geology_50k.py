"""Probe official GSI / Kerala government endpoints for 1:50,000 geology access.

Re-runnable probe written for RUN-2026-10-28-04. It answers one question with
evidence on disk: which of the official hosts are reachable TODAY, and what do
their services directories say, so that the ACCESS_RESTRICTED verdict recorded
in Phase 1 (bhukosh TCP refusals; Bhusanket 499 Token Required) is either
re-confirmed or overturned by current evidence.

Probed hosts (all official):
  bhukosh.gsi.gov.in      GSI public geoscience data portal (geology layers)
  bhusanket.gsi.gov.in    GSI Bhusanket (landslide reports + ArcGIS GIS Server)
  www.gsi.gov.in          GSI main site
  ngdr.gsi.gov.in         National Geoscience Data Repository (new portal)
  www.sdma.kerala.gov.in  Kerala KSDMA (hosts GSI-2022 district susceptibility shapefiles)

Writes data/interim/gsi_geology/probe_results.json with per-URL status, bytes,
error class and a short text head. A probe record is evidence, not proof of
dataset coverage.

Run:  python scripts/probe_gsi_geology_50k.py
"""
from __future__ import annotations

import json
import pathlib
import socket
import sys
import time

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "gsi_geology" / "probe_results.json"

H = {"User-Agent": "Mozilla/5.0 (RESQAI academic research probe)"}

PROBES: list[tuple[str, str]] = [
    ("bhukosh root", "https://bhukosh.gsi.gov.in/"),
    ("bhukosh public app", "https://bhukosh.gsi.gov.in/Bhukosh/Public"),
    ("bhusanket root", "https://bhusanket.gsi.gov.in/"),
    ("bhusanket arcgis services", "https://bhusanket.gsi.gov.in/gisserver/rest/services?f=json"),
    ("bhusanket arcgis token req", "https://bhusanket.gsi.gov.in/gisserver/tokens?f=json"),
    ("gsi main site", "https://www.gsi.gov.in/"),
    ("ngdr portal", "https://ngdr.gsi.gov.in/"),
    ("ngdr alt", "https://ngdr-gsi.gov.in/"),
    ("ksdma hazard maps", "https://sdma.kerala.gov.in/hazard-maps/"),
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rec: dict = {"dns": {}, "probes": []}
    for host in sorted({p.split("/")[2] for p in [u for _, u in PROBES]}):
        try:
            rec["dns"][host] = socket.gethostbyname(host)
        except OSError as e:
            rec["dns"][host] = f"DNS_FAIL: {type(e).__name__}: {e}"

    for label, url in PROBES:
        t0 = time.time()
        entry: dict = {"label": label, "url": url}
        try:
            r = requests.get(url, headers=H, timeout=25, allow_redirects=True)
            entry.update(status=r.status_code, bytes=len(r.content),
                         final_url=r.url, seconds=round(time.time() - t0, 1),
                         head=r.text[:300].replace("\n", " ")[:300])
        except requests.RequestException as e:
            entry.update(error=f"{type(e).__name__}: {e}", seconds=round(time.time() - t0, 1))
        rec["probes"].append(entry)
        print(f"{label:32s} -> {entry.get('status', entry.get('error'))} "
              f"({entry['seconds']}s, {entry.get('bytes', 0)} B)")

    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"written -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
