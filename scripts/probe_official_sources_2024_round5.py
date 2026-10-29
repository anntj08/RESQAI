"""Round-5 probes: NDMA landslide sub-pages (possible large dataset) and the
exact landslide-zip link list on the KSDMA hazard-maps page.

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
    ("ndma_landslide_0", "https://ndma.gov.in/en/landslide-0"),
    ("ndma_landslide_425mb", "https://ndma.gov.in/en/landslide-425-mb"),
    ("ndma_landslide_hazard_atlas_en_page", "https://ndma.gov.in/en/landslide-hazard-atlas"),
    ("ksdma_hazard_maps_zips", "https://sdma.kerala.gov.in/hazard-maps/"),
]

HREF_RE = re.compile(r'<a[^>]+href="([^"#]+)"[^>]*>(.*?)</a>', re.S | re.I)


def strip_html(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def main() -> int:
    results = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "probes": []}
    for key, url in PROBES:
        rec = {"key": key, "url": url}
        try:
            r = requests.get(url, headers=HDR, timeout=60, allow_redirects=True)
            rec["http_status"] = r.status_code
            rec["bytes"] = len(r.content)
            rec["final_url"] = r.url
            text = r.text
            if key == "ksdma_hazard_maps_zips":
                rec["zip_links"] = [{"href": h[:150], "text": strip_html(lab)[:60]}
                                    for h, lab in HREF_RE.findall(text)
                                    if h.lower().endswith(".zip")]
                rec["lsz_context"] = [re.sub(r"\s+", " ", m).strip() for m in
                                      re.findall(r"[^\n>]{0,120}(?:landslide|LSZ|susceptibility)"
                                                 r"[^\n<]{0,120}", text, re.I)][:12]
            else:
                links = [{"href": h[:150], "text": strip_html(lab)[:110]}
                         for h, lab in HREF_RE.findall(text)
                         if re.search(r"\.pdf|atlas|landslide|download|dataset|\.zip",
                                      h + " " + strip_html(lab), re.I)]
                seen, uniq = set(), []
                for l in links:
                    if l["href"] not in seen:
                        seen.add(l["href"])
                        uniq.append(l)
                rec["candidate_links"] = uniq[:50]
                body = re.sub(r"<script.*?</script>", "", text, flags=re.S)
                body = strip_html(body)
                m = re.search(r"(?i)(landslide[^.]{0,700})", body)
                rec["body_excerpt"] = m.group(1)[:700] if m else ""
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["probes"].append(rec)
        line = (f"{key}: HTTP {rec.get('http_status')} {rec.get('bytes')}B"
                if "http_status" in rec else f"{key}: FAIL {rec.get('error')}")
        print(line)

    (OUT / "official_sources_probe_round5.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
