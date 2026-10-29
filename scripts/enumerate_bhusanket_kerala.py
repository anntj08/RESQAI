"""Enumerate all Kerala entries in the on-disk Bhusanket report index.

RUN-2026-10-29-09 evidence step (read-only over data/raw). Prints accession
number, field season and title for every Kerala entry, so that anything
newer than the reports already on disk (e.g. 2024-25 / 2025-26 field-season
work on the July 2024 Wayanad disaster) can be identified by title.
"""
from __future__ import annotations

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "data" / "raw" / "landslide_inventory" / "gsi_bhusanket" / "LandslideReport.json"


def parse_index(txt: str) -> list:
    body = txt.split("=", 1)[1].strip().rstrip(";")
    body = re.sub(r"^\s*LandslideReportData.*$", "", body, flags=re.M)
    body = re.sub(r"//[^\n]*", "", body)
    body = re.sub(r",(\s*[}\]])", r"\1", body)
    return json.loads(body)


def main() -> int:
    recs = parse_index(INDEX.read_text(encoding="utf-8", errors="replace"))
    ker = [r for r in recs if "kerala" in json.dumps(r, ensure_ascii=False).lower()]
    print(f"total: {len(recs)} | kerala entries: {len(ker)}")
    for r in ker:
        acc = str(r.get("Acc. No.", ""))
        fs = str(r.get("Field Season", ""))
        t = str(r.get("Title of the project", ""))[:100]
        print(f"  {acc:>30} | FS {fs:<9} | {t}")
    # anything with a field season of 2024-25 or later, any state (for context)
    late = [r for r in recs if re.search(r"202[4-9]-20?[2-9]", str(r.get("Field Season", "")))]
    print(f"\nfield seasons 2024-25 or later, all states: {len(late)}")
    for r in late:
        acc = str(r.get("Acc. No.", ""))
        fs = str(r.get("Field Season", ""))
        st = str(r.get("State", ""))
        t = str(r.get("Title of the project", ""))[:88]
        print(f"  {acc:>28} | FS {fs:<9} | {st:<16} | {t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
