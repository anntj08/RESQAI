"""Display round-2 probe links and the KSDMA document assessment summaries.

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

r2 = json.loads((E / "official_sources_probe_round2.json").read_text(encoding="utf-8"))
for p in r2["probes"]:
    print(f"\n=== {p['key']} -> HTTP {p.get('http_status')} | hits: {p.get('text_hits', {})}")
    for item in p.get("candidate_links", [])[:45]:
        print(f"    {item['href'][:120]}  |  {item['text'][:85]}")

print("\n\n########## KSDMA DOCUMENT ASSESSMENT ##########")
a = json.loads((E / "ksdma_documents_assessment.json").read_text(encoding="utf-8"))
for d in a["documents"]:
    print(f"\n=== {d['key']} | HTTP {d.get('http_status')} | {d.get('bytes')}B "
          f"| pages={d.get('pages')} | chars={d.get('extracted_chars')}")
    if d.get("first_300_chars"):
        print("  head:", d["first_300_chars"][:280])
    if d.get("pattern_counts"):
        print("  pattern_counts:", d["pattern_counts"])
    for s in d.get("context_samples", []):
        print("    ctx:", s[:170])
    if d.get("raw_text_preview"):
        print("  raw_text_preview:", d["raw_text_preview"][:160])
