"""Probe the NGDR portal (www.geodataindia.gov.in) for 1:50,000 geology access.

NGDR (National Geoscience Data Repository, GSI nodal agency / BISAG-N integrator)
lists a "Standard Geological Map (1:50K)" product (5,087 toposheets, 32.7 lakh km2)
in its official brochure (mines.gov.in/admin/download/65e1c382744241709294466.pdf).
This probe records, with evidence on disk, what is reachable anonymously TODAY:
the portal root, the login page, and whether any OGC/ArcGIS map services are
exposed without authentication. A probe record is evidence, not coverage proof.

Writes data/interim/gsi_geology/ngdr_probe.json.

Run:  python scripts/probe_ngdr_geodata.py
"""
from __future__ import annotations

import json
import pathlib
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "gsi_geology" / "ngdr_probe.json"
H = {"User-Agent": "Mozilla/5.0 (RESQAI academic research probe)"}

PROBES: list[tuple[str, str]] = [
    ("root", "https://www.geodataindia.gov.in/"),
    ("login", "https://www.geodataindia.gov.in/login"),
    ("geoserver web", "https://www.geodataindia.gov.in/geoserver/web/"),
    ("geoserver rest layers", "https://www.geodataindia.gov.in/geoserver/rest/layers.json"),
    ("arcgis services", "https://www.geodataindia.gov.in/server/rest/services?f=json"),
    ("gisserver services", "https://www.geodataindia.gov.in/gisserver/rest/services?f=json"),
    ("api datasets", "https://www.geodataindia.gov.in/api/datasets"),
]


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rec: list[dict] = []
    for label, url in PROBES:
        entry: dict = {"label": label, "url": url}
        try:
            r = requests.get(url, headers=H, timeout=25, allow_redirects=True)
            entry.update(status=r.status_code, bytes=len(r.content), final_url=r.url,
                         head=r.text[:400].replace("\n", " ")[:400])
        except requests.RequestException as e:
            entry.update(error=f"{type(e).__name__}: {e}")
        rec.append(entry)
        print(f"{label:22s} -> {entry.get('status', entry.get('error'))} "
              f"({entry.get('bytes', 0)} B)")
    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"written -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
