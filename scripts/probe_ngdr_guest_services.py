"""Inspect the NGDR guest viewer for anonymously accessible map services.

geodataindia.gov.in serves a guest map viewer (Guest user tier = VISUALIZATION
only, per the official tier table). This script fetches the viewer HTML and its
scripts, extracts every candidate OGC/ArcGIS service endpoint referenced in
page assets, and probes each anonymously with GetCapabilities / f=json. The
purpose is to establish whether the 1:50K Standard Geological Map layers can be
listed (and their spatial coverage queried) WITHOUT an account — i.e. whether
the guest tier exposes OGC services that later steps could use.

Writes data/interim/gsi_geology/ngdr_guest_services.json.

Run:  python scripts/probe_ngdr_guest_services.py
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "gsi_geology" / "ngdr_guest_services.json"
H = {"User-Agent": "Mozilla/5.0 (RESQAI academic research probe)"}
BASE = "https://www.geodataindia.gov.in"

# patterns that look like map-service endpoints in web-app assets
PAT = re.compile(
    r"""(?:https?://[^\s"''<>]+?|(?:/[A-Za-z0-9_./-]+?))"""
    r"""(?:geoserver|gisserver|server|arcgis|wms|wfs|mapserver|ows)[^\s"'<>]*""",
    re.IGNORECASE)


def probe(url: str) -> dict:
    e: dict = {"url": url}
    try:
        r = requests.get(url, headers=H, timeout=25, allow_redirects=True)
        e.update(status=r.status_code, bytes=len(r.content),
                 content_type=r.headers.get("content-type", ""))
        body = r.text
        caps = []
        for key in ("ServiceException", "WMS_Capabilities", "WFS_Capabilities",
                    "currentVersion", "services", "Layer", "NameLayer"):
            if key.lower() in body.lower():
                caps.append(key)
        e["markers"] = caps
        e["head"] = body[:600].replace("\n", " ")[:600]
    except requests.RequestException as ex:
        e["error"] = f"{type(ex).__name__}: {ex}"
    return e


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    rec: dict = {"assets_fetched": [], "candidate_endpoints": [], "probes": []}
    seen: set[str] = set()

    pages = [f"{BASE}/guestuser", f"{BASE}/login"]
    for page in pages:
        try:
            r = requests.get(page, headers=H, timeout=30)
            html = r.text
            rec["assets_fetched"].append({"url": page, "status": r.status_code,
                                          "bytes": len(r.content)})
            for m in PAT.findall(html):
                cand = m.strip("\\'\"")
                if cand not in seen:
                    seen.add(cand)
        except requests.RequestException as ex:
            rec["assets_fetched"].append({"url": page, "error": f"{type(ex).__name__}: {ex}"})

    # resolve relative candidates to absolute
    abs_candidates = []
    for c in sorted(seen):
        if c.startswith("/"):
            abs_candidates.append(BASE + c)
        elif c.startswith("http"):
            abs_candidates.append(c)
    rec["candidate_endpoints"] = abs_candidates

    # deduplicate to a probe-able shortlist: capillary paths with service words
    short = [c for c in abs_candidates
             if any(k in c.lower() for k in ("wms", "wfs", "geoserver", "gisserver",
                                             "mapserver", "rest/", "ows"))][:40]
    for c in short:
        for suffix in ("" , "?f=json", "?service=WMS&version=1.3.0&request=GetCapabilities"):
            u = c + suffix
            if "?" in c and suffix:
                u = c + "&" + suffix[1:]
            rec["probes"].append(probe(u))
            print(f"probe {u[:110]} -> "
                  f"{rec['probes'][-1].get('status', rec['probes'][-1].get('error'))}")

    OUT.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print(f"written -> {OUT.relative_to(ROOT)} ({len(rec['probes'])} probes, "
          f"{len(abs_candidates)} candidate endpoints)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
