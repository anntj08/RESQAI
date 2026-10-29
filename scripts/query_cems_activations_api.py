"""Query the public CEMS On-Demand Mapping activations API (discovered from the
grid's network traffic) for Wayanad / India landslide-relevant activations.

RUN-2026-10-29-09 evidence step: catalogue metadata only (activation codes,
titles, dates, countries) saved to the review evidence directory. No inventory
data, no maps, no product downloads.
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
BASE = ("https://mapping.emergency.copernicus.eu/activations/api/activations/"
        "?categories=fire%2Cvolcan%2Cearthquake%2Cmass%2Cstorm%2Cflood%2C"
        "humanitarian%2Cindustrial%2Cenvironment%2Cother&services=&closed=")

QUERIES = [
    ("q_wayanad_alltime", f"{BASE}&activationTime=2012-01%2C2026-10-29&q=Wayanad&limit=100&offset=0"),
    ("india_mass_movement", f"{BASE}&activationTime=2012-01%2C2026-10-29&countries=India&q=&limit=100&offset=0"),
    ("india_window_jul2024", f"{BASE}&activationTime=2024-07-01%2C2024-08-31&countries=India&q=&limit=100&offset=0"),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "api_base": "https://mapping.emergency.copernicus.eu/activations/api/activations/",
               "queries": {}}
    for key, url in QUERIES:
        r = requests.get(url, headers=HDR, timeout=60)
        rec = {"url": url, "http_status": r.status_code, "bytes": len(r.content)}
        try:
            data = r.json()
            rows = data.get("results", data.get("data", []))
            count = data.get("count", len(rows))
            slim = [{"code": x.get("code") or x.get("event_code"),
                     "title": x.get("title") or x.get("event_title"),
                     "date": x.get("activation_time") or x.get("date"),
                     "type": x.get("event_type") or x.get("category"),
                     "country": x.get("country") or x.get("countries")}
                    for x in rows]
            rec.update({"count_reported": count, "rows_returned": len(rows),
                        "rows": slim[:40]})
            print(f"== {key}: HTTP {r.status_code}, count={count}, returned={len(rows)}")
            for s in slim[:40]:
                print("   ", json.dumps(s, ensure_ascii=False)[:200])
        except Exception as exc:  # noqa: BLE001
            rec["parse_error"] = repr(exc)
            rec["preview"] = r.text[:300]
            print(f"== {key}: HTTP {r.status_code} parse-fail {exc}")
        summary["queries"][key] = rec
        (OUT / f"cems_api_{key}.json").write_text(
            json.dumps(rec, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (OUT / "cems_api_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("evidence ->", OUT.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
