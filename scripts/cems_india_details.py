"""Fetch detail records for the CEMS activations whose titles mention India,
plus a q=Kerala check, and re-test the countries filter formats.

RUN-2026-10-29-09 evidence step (catalogue metadata only).
"""
from __future__ import annotations

import json
import pathlib
import sys
from datetime import datetime, timezone

import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"
HDR = {"User-Agent": "RESQAI-research/1.0 (academic use)", "Accept": "application/json"}
BASE = "https://mapping.emergency.copernicus.eu/activations/api/activations/"

results = {"generated_utc": datetime.now(timezone.utc).isoformat(), "details": {},
           "q_kerala": None, "countries_filter_tests": {}}

for code in ["EMSR357", "EMSR104", "EMSR057", "EMSR054", "EMSR049"]:
    r = requests.get(f"{BASE}{code}/", headers=HDR, timeout=60)
    if r.status_code == 200:
        d = r.json()
        results["details"][code] = {
            "name": d.get("name"), "category": (d.get("category") or {}).get("name"),
            "countries": [c.get("short_name") for c in d.get("countries", [])],
            "activationTime": d.get("activationTime"), "n_aois": d.get("n_aois"),
            "n_products": d.get("n_products"),
            "centroid": d.get("centroid")}
        print(f"{code}: {d.get('name')} | {(d.get('category') or {}).get('name')} | "
              f"{d.get('activationTime')} | products={d.get('n_products')}")
    else:
        results["details"][code] = {"http_status": r.status_code}
        print(code, r.status_code)

LIST = (BASE + "?categories=fire%2Cvolcan%2Cearthquake%2Cmass%2Cstorm%2Cflood%2C"
        "humanitarian%2Cindustrial%2Cenvironment%2Cother&services=&closed="
        "&activationTime=2012-01%2C2026-10-29&limit=100&offset=0")
for label, url in [("q_kerala", LIST + "&q=Kerala"),
                   ("countries_India", LIST + "&countries=India"),
                   ("countries_IND", LIST + "&countries=IND")]:
    r = requests.get(url, headers=HDR, timeout=60)
    try:
        d = r.json()
        results[label if label != "q_kerala" else "q_kerala"] = {
            "count": d.get("count"),
            "codes": [x.get("code") for x in d.get("results", [])]}
        print(label, "->", d.get("count"))
    except Exception as exc:  # noqa: BLE001
        results["countries_filter_tests"][label] = {"error": repr(exc)}
        print(label, "err", exc)

(OUT / "cems_api_india_details.json").write_text(
    json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("evidence ->", OUT.name)
