"""Display round-4 probe results (Wayanad DDMA, NDMA, CEMS JS surface).

RUN-2026-10-29-09 evidence display helper (read-only).
"""
from __future__ import annotations

import json
import pathlib
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"

r4 = json.loads((E / "official_sources_probe_round4.json").read_text(encoding="utf-8"))
for p in r4["probes"]:
    print(f"\n=== {p['key']} -> HTTP {p.get('http_status')} | hits: {p.get('text_hits', {})}")
    for item in p.get("candidate_links", [])[:40]:
        print(f"    {item['href'][:125]}  |  {item['text'][:90]}")
    if p.get("script_srcs"):
        print("  js bundles:", p["script_srcs"])
    if p.get("api_strings"):
        print("  api strings:", p["api_strings"])
for t in r4["cems_api_tries"]:
    print(f"\nCEMS try: {t['url']} -> {t.get('http_status')} {t.get('bytes')}B "
          f"ct={t.get('content_type', '')} {t.get('preview', '')[:100]}")
