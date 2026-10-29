"""Review the on-disk GSI Bhusanket report index for Kerala/Wayanad entries.

RUN-2026-10-29-09 evidence step. Read-only over data/raw (nothing modified).
Answers, from the index JSON downloaded in phase 1/2:
  * total reports, Kerala reports, Wayanad-related titles;
  * field-season/report-year for each Wayanad entry;
  * whether anything newer than the 10 Wayanad PDFs already on disk exists
    (e.g. 2024-25 season reports on the July 2024 disaster).
Also refreshes the live index (metadata catalogue only - report titles and
accession numbers, NOT inventory records) and diffs it against the on-disk copy;
the refreshed copy is saved to data/interim/ as evidence.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "raw" / "landslide_inventory" / "gsi_bhusanket" / "LandslideReport.json"
OUT = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"
URL = "https://bhusanket.gsi.gov.in/json/LandslideReport/LandslideReport.json"
HDR = {"User-Agent": "RESQAI-research/1.0 (academic use)"}


def records(d):
    if isinstance(d, list):
        return d
    for k in ("data", "records", "reports", "LandslideReports"):
        if isinstance(d, dict) and isinstance(d.get(k), list):
            return d[k]
    return []


def blob(r) -> str:
    return json.dumps(r, ensure_ascii=False)


def parse_index(txt: str) -> list:
    """Normalize the Bhusanket JS catalogue to JSON (phase-1 recipe, scripts/parse_bhusanket.py)."""
    body = txt.split("=", 1)[1].strip().rstrip(";")
    body = re.sub(r"^\s*LandslideReportData.*$", "", body, flags=re.M)
    body = re.sub(r"//[^\n]*", "", body)              # strip // comments
    body = re.sub(r",(\s*[}\]])", r"\1", body)        # trailing commas
    return json.loads(body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    recs = parse_index(INDEX.read_text(encoding="utf-8", errors="replace"))
    print(f"on-disk index: {len(recs)} report records")

    ker = [r for r in recs if "kerala" in blob(r).lower()]
    wyd = [r for r in ker if "wayanad" in blob(r).lower() or re.search(r"\bwyd\b", blob(r).lower())]
    print(f"kerala: {len(ker)} | wayanad-related: {len(wyd)}")
    for r in wyd:
        b = blob(r)
        m = re.search(r'"(?:title|report_title|ReportTitle|name)"\s*:\s*"([^"]+)"', b)
        y = re.search(r'"(?:year|fs|field_season|report_year|acc_year)"\s*:\s*"?([0-9]{4}[^,"]*)', b)
        a = re.search(r'"(?:acc|acc_no|accession|AccNo|account_no|accno)"\s*:\s*"?([^,"}]+)', b)
        print(f"- title={m.group(1) if m else b[:90]!r} | year={y.group(1) if y else '?'} | acc={a.group(1) if a else '?'}")

    summary = {"on_disk_total": len(recs), "on_disk_kerala": len(ker), "on_disk_wayanad": len(wyd)}

    # live refresh (catalogue metadata only)
    try:
        r = requests.get(URL, headers=HDR, timeout=60)
        print(f"\nlive index: HTTP {r.status_code}, {len(r.content)} bytes")
        summary["live_http_status"] = r.status_code
        summary["live_bytes"] = len(r.content)
        if r.status_code == 200:
            (OUT / "LandslideReport_live_2026-10-29.json").write_bytes(r.content)
            live = parse_index(r.content.decode("utf-8", errors="replace"))
            summary["live_total"] = len(live)
            live_ker = [x for x in live if "kerala" in blob(x).lower()]
            live_wyd = [x for x in live_ker
                        if "wayanad" in blob(x).lower() or re.search(r"\bwyd\b", blob(x).lower())]
            summary["live_kerala"] = len(live_ker)
            summary["live_wayanad"] = len(live_wyd)
            disk_keys = {re.sub(r"\s+", " ", blob(x).lower())[:200] for x in wyd}
            new_wyd = [x for x in live_wyd
                       if re.sub(r"\s+", " ", blob(x).lower())[:200] not in disk_keys]
            summary["live_wayanad_new_vs_disk"] = len(new_wyd)
            for x in new_wyd[:10]:
                print("NEW wayanad entry:", blob(x)[:220])
        else:
            summary["live_note"] = r.text[:200]
    except Exception as exc:  # noqa: BLE001 - evidence run must not crash
        summary["live_error"] = repr(exc)
        print("live fetch failed:", exc)

    (OUT / "bhusanket_index_review.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"\nevidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
