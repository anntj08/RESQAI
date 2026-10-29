"""Display the RUN-2026-10-29-09 official-source probe results.

Reads data/interim/inventory_source_review_2026-10-29/official_sources_probe.json
and prints the extracted candidate links / context snippets per probe, so the
discovery note can cite exact URLs. Read-only helper.
"""
from __future__ import annotations

import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"

d = json.loads((E / "official_sources_probe.json").read_text(encoding="utf-8"))

for p in d["probes"]:
    print(f"\n=== {p['key']} -> HTTP {p.get('http_status')} ({p.get('bytes')}B)"
          if "http_status" in p else f"\n=== {p['key']} -> FAIL: {p.get('error', '')[:110]}")
    for k in ("candidate_links", "wayanad_context", "activation_links", "text_hits"):
        if p.get(k):
            print(f"  {k}:")
            for item in p[k]:
                if isinstance(item, dict):
                    print(f"    {item.get('href', '')[:130]}  |  {item.get('text', '')[:90]}")
                else:
                    print(f"    {str(item)[:150]}")
