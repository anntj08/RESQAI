"""Round-4 (final) probes: Wayanad DDMA orders/reports pages, NDMA English
landslide page, and the CEMS activations portal API surface.

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
    ("wayanad_dm_orders", "https://wayanad.gov.in/en/dm-orders/",
     r"\.pdf|landslide|2024|chooralmala|chooral|munda|meppadi|report|order"),
    ("wayanad_disaster_page", "https://wayanad.gov.in/en/disaster-management-2/",
     r"\.pdf|landslide|2024|chooralmala|chooral|munda|meppadi|report"),
    ("ndma_landslide_en", "https://ndma.gov.in/en/landslide",
     r"\.pdf|atlas|guideline|landslide|2024|report"),
    ("cems_activations_page", "https://mapping.emergency.copernicus.eu/activations/",
     None),
]

# candidate CEMS API endpoints (documented guesses, status-only evidence)
CEMS_API_TRIES = [
    "https://mapping.emergency.copernicus.eu/api/activations",
    "https://mapping.emergency.copernicus.eu/jsonapi/node/activation",
    "https://mapping.emergency.copernicus.eu/api/v1/activations",
]

HREF_RE = re.compile(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', re.S | re.I)


def strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    results = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "probes": [], "cems_api_tries": []}
    for key, url, pat in PROBES:
        rec = {"key": key, "url": url}
        try:
            r = requests.get(url, headers=HDR, timeout=60, allow_redirects=True)
            rec["http_status"] = r.status_code
            rec["bytes"] = len(r.content)
            rec["final_url"] = r.url
            text = r.text
            if pat:
                links = [{"href": h[:150], "text": strip_html(lab)[:110]}
                         for h, lab in HREF_RE.findall(text)
                         if re.search(pat, h + " " + strip_html(lab), re.I)]
                seen, uniq = set(), []
                for l in links:
                    if l["href"] not in seen:
                        seen.add(l["href"])
                        uniq.append(l)
                rec["candidate_links"] = uniq[:80]
                low = text.lower()
                rec["text_hits"] = {w: low.count(w)
                                    for w in ("wayanad", "chooralmala", "mundakkai",
                                              "meppadi", "landslide", "2024")
                                    if w in low}
            else:  # CEMS activations page: look for data endpoints in the JS bundle refs
                rec["script_srcs"] = sorted(set(re.findall(
                    r'src="([^"]+\.js[^"]*)"', text)))[:10]
                rec["api_strings"] = sorted(set(re.findall(
                    r'["\']([^"\']*(?:api|jsonapi|rest)[^"\']*)["\']', text, re.I)))[:20]
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["probes"].append(rec)
        line = (f"{key}: HTTP {rec.get('http_status')} {rec.get('bytes')}B"
                if "http_status" in rec else f"{key}: FAIL {rec.get('error')}")
        print(line)

    for url in CEMS_API_TRIES:
        rec = {"url": url}
        try:
            r = requests.get(url, headers=HDR, timeout=30)
            rec["http_status"] = r.status_code
            rec["bytes"] = len(r.content)
            rec["content_type"] = r.headers.get("content-type", "")
            rec["preview"] = r.text[:150].replace("\n", " ")
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["cems_api_tries"].append(rec)
        print(f"CEMS API {url} -> {rec.get('http_status', rec.get('error'))}")

    (OUT / "official_sources_probe_round4.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
