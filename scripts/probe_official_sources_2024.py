"""Probe official sources for a Wayanad July-2024 multi-event landslide inventory.

RUN-2026-10-29-09 evidence step (documentation/research only; websearch is
unavailable this session, so each candidate source is probed directly).

What this does:
  * records HTTP reachability/failure mode for every candidate portal;
  * extracts candidate links (PDFs, disaster/landslide pages, activation lists)
    from the KSDMA 2024-reports, hazard-maps and event-maps pages and from the
    district/NRSC/Copernicus roots;
  * saves a consolidated evidence JSON + log to
    data/interim/inventory_source_review_2026-10-29/.

What this does NOT do: download, digitize, merge or alter inventory data; touch
the manifest; or modify any Phase 4/5 output. Link lists and status codes are
catalogue-level evidence only.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

import requests

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"
HDR = {"User-Agent": "RESQAI-research/1.0 (academic use)", "Accept-Language": "en"}

# (key, url, what to extract)
PROBES = [
    ("gsi_bhusanket_live_index",
     "https://bhusanket.gsi.gov.in/json/LandslideReport/LandslideReport.json",
     "none"),
    ("gsi_bhukosh", "https://bhukosh.gsi.gov.in/", "none"),
    ("gsi_portal", "https://www.gsi.gov.in/", "none"),
    ("nrsc_bhuvan_landslide_atlas",
     "https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=ls", "wayanad"),
    ("nrsc_root", "https://www.nrsc.gov.in/", "wayanad"),
    ("wayanad_district_root", "https://wayanad.gov.in/", "disaster"),
    ("ndma_root", "https://ndma.gov.in/", "wayanad"),
    ("nidm_root", "https://nidm.gov.in/", "wayanad"),
    ("kerala_dmsuite", "https://dmsuite.kerala.gov.in/", "none"),
    ("copernicus_ems_root", "https://emergency.copernicus.eu/", "activation"),
    ("copernicus_ems_list_old",
     "https://emergency.copernicus.eu/mapping/list-of-activations-rapid", "none"),
    ("copernicus_ems_list_alt", "https://emergency.copernicus.eu/activations", "wayanad"),
    ("ksdma_hazard_maps", "https://sdma.kerala.gov.in/hazard-maps/", "links"),
    ("ksdma_reports_landslides_2024", "https://sdma.kerala.gov.in/reports-landslides-2024/",
     "links"),
    ("ksdma_event_specific_maps", "https://sdma.kerala.gov.in/event-specific-maps/",
     "links"),
]

HREF_RE = re.compile(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', re.S | re.I)


def strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "probes": []}
    for key, url, mode in PROBES:
        rec = {"key": key, "url": url}
        try:
            r = requests.get(url, headers=HDR, timeout=40, allow_redirects=True)
            rec["http_status"] = r.status_code
            rec["bytes"] = len(r.content)
            rec["final_url"] = r.url
            text = r.text
            if mode == "links":
                links = []
                for href, label in HREF_RE.findall(text):
                    lab = strip_html(label)
                    if href.endswith(".pdf") or href.endswith(".zip") or \
                       "2024" in lab or "landslide" in lab.lower() or \
                       "hazard" in lab.lower() or "map" in lab.lower():
                        links.append({"href": href, "text": lab[:140]})
                rec["candidate_links"] = links[:60]
            elif mode == "wayanad":
                hits = []
                low = text.lower()
                for pat in ("wayanad", "landslide", "activations"):
                    n = low.count(pat)
                    if n:
                        hits.append(f"{pat}: {n}")
                rec["text_hits"] = hits
                m = re.findall(r"[^\n>]{0,90}wayanad[^\n<]{0,90}", low)
                rec["wayanad_context"] = [strip_html(x) for x in m[:8]]
            elif mode == "disaster":
                links = [{"href": h, "text": strip_html(lab)[:90]}
                         for h, lab in HREF_RE.findall(text)
                         if re.search(r"disaster|landslide|2024", h + strip_html(lab), re.I)]
                rec["candidate_links"] = links[:40]
            elif mode == "activation":
                m = re.findall(r'href="([^"]*activ[^"]*)"', text, re.I)
                rec["activation_links"] = sorted(set(m))[:12]
        except Exception as exc:  # noqa: BLE001 - each probe must fail independently
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["probes"].append(rec)
        line = (f"{key}: HTTP {rec.get('http_status')} {rec.get('bytes')}B"
                if "http_status" in rec else f"{key}: FAIL {rec.get('error')}")
        print(line)

    (OUT / "official_sources_probe.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
