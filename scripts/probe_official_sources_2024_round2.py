"""Round-2 probes: pages discovered in the round-1 KSDMA menus plus deeper
link extraction for NRSC Bhuvan, NDMA, dmsuite, wayanad.gov.in and Copernicus.

RUN-2026-10-29-09 evidence step. Catalogue-level evidence only (status codes,
link lists, context snippets) saved to the review evidence directory.
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

# (key, url, mode)  modes: links | links_wayanad | nav
PROBES = [
    ("ksdma_landslides_2024_page", "https://sdma.kerala.gov.in/landslides-2024/", "links"),
    ("ksdma_event_2024_page", "https://sdma.kerala.gov.in/event-2024-2/", "links"),
    ("ksdma_meppadi_2024_csr_page", "https://sdma.kerala.gov.in/meppadi-2024-csr/", "links"),
    ("ksdma_maps_page", "https://sdma.kerala.gov.in/maps-2/", "links"),
    ("nrsc_bhuvan_atlas_links",
     "https://bhuvan-app1.nrsc.gov.in/disaster/disaster.php?id=ls", "links"),
    ("ndma_landslide_links", "https://ndma.gov.in/", "links_wayanad"),
    ("dmsuite_links", "https://dmsuite.kerala.gov.in/", "links_wayanad"),
    ("wayanad_district_links", "https://wayanad.gov.in/", "links_wayanad"),
    ("copernicus_root_nav", "https://emergency.copernicus.eu/", "links"),
    ("copernicus_mapping_no_slash", "https://emergency.copernicus.eu/mapping", "nav"),
    ("copernicus_list_no_rapid",
     "https://emergency.copernicus.eu/mapping/list-of-activations", "nav"),
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
            if mode in ("links", "links_wayanad"):
                pat = (r"landslide|2024|wayanad|hazard|lsz|disaster"
                       if mode == "links_wayanad"
                       else r"\.pdf|\.zip|landslide|wayanad|2024|lsz|atlas|app|\.js")
                links = [{"href": h[:150], "text": strip_html(lab)[:110]}
                         for h, lab in HREF_RE.findall(text)
                         if re.search(pat, h + " " + strip_html(lab), re.I)]
                # de-duplicate by href, keep order
                seen, uniq = set(), []
                for l in links:
                    if l["href"] not in seen:
                        seen.add(l["href"])
                        uniq.append(l)
                rec["candidate_links"] = uniq[:80]
                low = text.lower()
                rec["text_hits"] = {w: low.count(w)
                                    for w in ("wayanad", "landslide", "2024")
                                    if w in low}
            else:  # nav
                m = re.findall(r'href="([^"]+)"', text)
                rec["hrefs"] = sorted(set(m))[:40]
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["probes"].append(rec)
        line = (f"{key}: HTTP {rec.get('http_status')} {rec.get('bytes')}B"
                if "http_status" in rec else f"{key}: FAIL {rec.get('error')}")
        print(line)

    (OUT / "official_sources_probe_round2.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
