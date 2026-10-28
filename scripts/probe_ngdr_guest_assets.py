"""Fetch the NGDR guest-viewer HTML + its JS bundles and extract service URLs.

The guest map viewer is a JS application; its OGC/ArcGIS endpoints are referenced
from bundle files, not the HTML. This script:

  1. fetches https://www.geodataindia.gov.in/guestuser (saves the HTML),
  2. collects .js bundle URLs from <script src> / <link href>,
  3. fetches each bundle (saved under data/interim/gsi_geology/ngdr_assets/),
  4. greps HTML + bundles for absolute/relative map-service endpoints,
  5. writes the endpoint list to data/interim/gsi_geology/ngdr_asset_endpoints.json.

Run:  python scripts/probe_ngdr_guest_assets.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "gsi_geology" / "ngdr_asset_endpoints.json"
ASSETS = ROOT / "data" / "interim" / "gsi_geology" / "ngdr_assets"
BASE = "https://www.geodataindia.gov.in"
H = {"User-Agent": "Mozilla/5.0 (RESQAI academic research probe)"}

URL_RE = re.compile(
    r"""["']((?:https?:)?//[^"'\s]{8,160}|/(?:[A-Za-z0-9_.\-]+/)+"""
    r"""(?:geoserver|gisserver|server|arcgis|ows|proxy|api)[^"'\s]{0,120})["']""",
    re.IGNORECASE)
SERVICE_HINTS = ("wms", "wfs", "geoserver", "gisserver", "mapserver", "arcgis",
                 "rest/", "ows", "tms", "wmts")


def main() -> int:
    ASSETS.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rec: dict = {"pages": [], "bundles": [], "endpoints": []}
    seen: set[str] = set()

    page = requests.get(f"{BASE}/guestuser", headers=H, timeout=30)
    (ASSETS / "guestuser.html").write_bytes(page.content)
    rec["pages"].append({"url": f"{BASE}/guestuser", "status": page.status_code,
                         "bytes": len(page.content)})
    html = page.text
    bundles = sorted({u for u in re.findall(r'(?:src|href)=["\']([^"\']+\.js[^"\']*)["\']', html)})

    for b in bundles[:20]:
        url = b if b.startswith("http") else BASE + ("" if b.startswith("/") else "/") + b
        try:
            r = requests.get(url, headers=H, timeout=30)
            name = "bundle_" + re.sub(r"[^A-Za-z0-9_.]", "_", url.split("/")[-1])[:60]
            (ASSETS / name).write_bytes(r.content)
            rec["bundles"].append({"url": url, "status": r.status_code, "bytes": len(r.content)})
            for m in URL_RE.findall(r.content.decode("utf-8", "replace")):
                if m not in seen:
                    seen.add(m)
        except requests.RequestException as e:
            rec["bundles"].append({"url": url, "error": f"{type(e).__name__}: {e}"})

    for m in URL_RE.findall(html):
        seen.add(m)

    endpoints = []
    for c in sorted(seen):
        low = c.lower()
        if any(h in low for h in SERVICE_HINTS):
            endpoints.append(c if c.startswith("http") else BASE + c)
    rec["endpoints"] = endpoints
    for e in endpoints:
        print("endpoint:", e[:130])
    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"bundles fetched: {len(rec['bundles'])}; service-like endpoints: {len(endpoints)}")
    print(f"written -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
