"""Round-3 probes: NDMA Landslide Hazard Atlas node, dmsuite redirect check,
Wayanad DDMA English site, and the new CEMS rapid-mapping portal.

RUN-2026-10-29-09 evidence step (catalogue-level only).
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
HDR = {"User-Agent": "RESQAI-research/1.0 (academic use)"}

PROBES = [
    ("ndma_landslide_hazard_atlas_en", "https://ndma.gov.in/node/84", "links"),
    ("ndma_landslide_node_en", "https://ndma.gov.in/node/132", "links"),
    ("dmsuite_redirect_check", "https://dmsuite.kerala.gov.in/", "redirect"),
    ("wayanad_ddma_english", "https://wayanad.gov.in/en/", "links_wayanad"),
    ("cems_rapidmapping_root", "https://rapidmapping.emergency.copernicus.eu/", "links"),
    ("cems_on_demand_root", "https://mapping.emergency.copernicus.eu/", "links"),
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
                pat = (r"landslide|wayanad|hazard|atlas|disaster|2024"
                       if mode == "links_wayanad"
                       else r"landslide|wayanad|atlas|\.pdf|activat|EMSR|inventory")
                links = [{"href": h[:150], "text": strip_html(lab)[:110]}
                         for h, lab in HREF_RE.findall(text)
                         if re.search(pat, h + " " + strip_html(lab), re.I)]
                seen, uniq = set(), []
                for l in links:
                    if l["href"] not in seen:
                        seen.add(l["href"])
                        uniq.append(l)
                rec["candidate_links"] = uniq[:60]
                low = text.lower()
                rec["text_hits"] = {w: low.count(w)
                                    for w in ("wayanad", "landslide", "inventory",
                                              "atlas", "2024") if w in low}
            elif mode == "redirect":
                low = text.lower()
                rec["text_hits"] = {w: low.count(w)
                                    for w in ("wayanad", "landslide", "ddma") if w in low}
                rec["title"] = (re.search(r"<title>([^<]*)</title>", text, re.I).group(1)
                                if re.search(r"<title>([^<]*)</title>", text, re.I) else None)
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["probes"].append(rec)
        line = (f"{key}: HTTP {rec.get('http_status')} {rec.get('bytes')}B -> "
                f"{rec.get('final_url', '')[:80]}"
                if "http_status" in rec else f"{key}: FAIL {rec.get('error')}")
        print(line)

    (OUT / "official_sources_probe_round3.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
