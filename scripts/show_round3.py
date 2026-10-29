"""Display round-3 probe results.

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

r3 = json.loads((E / "official_sources_probe_round3.json").read_text(encoding="utf-8"))
for p in r3["probes"]:
    print(f"\n=== {p['key']} -> HTTP {p.get('http_status')} | final: "
          f"{p.get('final_url', '')[:100]} | hits: {p.get('text_hits', {})}")
    if p.get("title"):
        print("  page title:", p["title"])
    for item in p.get("candidate_links", [])[:40]:
        print(f"    {item['href'][:125]}  |  {item['text'][:90]}")
