"""Assess the two KSDMA 'Reports - Landslides 2024' documents not yet on disk,
plus verify the nature of the go_ms6 PDF.

RUN-2026-10-29-09 evidence step.

Scope note (run constraint): this is a candidate-source *assessment* only.
The PDFs are saved to data/interim/inventory_source_review_2026-10-29/ as
review evidence; nothing is merged into the inventory, no CSVs are produced
from them, and manifest statuses are untouched. The goal is to classify each
document as discussion-report vs geospatial inventory by inspecting its text
for coordinate/location-table structures.

Docs assessed:
  * FPS2025.pdf - 'Meeting the Essential SRH Needs of Communities Affected by
    Landslides - Wayanad, Kerala' (uploaded 2026/03)
  * Environment-Committee-2025.pdf - 15th Kerala Legislative Assembly,
    Committee on Environment (2023-2026), 13th Report (uploaded 2026/02)
  * data/raw/landslide_inventory/ksdma/ksdma_go_ms6_dmd_gsi.pdf - prior phase
    acquisition whose 44-byte text extract was never explained.
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

import pypdf

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"
HDR = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
BASE = "https://sdma.kerala.gov.in"

DOCS = [
    ("ksdma_fps2025_srh_needs", f"{BASE}/wp-content/uploads/2026/03/FPS2025.pdf"),
    ("ksdma_environment_committee_13th_report",
     f"{BASE}/wp-content/uploads/2026/02/Environment-Committee-2025.pdf"),
]

GO_MS6 = ROOT / "data" / "raw" / "landslide_inventory" / "ksdma" / "ksdma_go_ms6_dmd_gsi.pdf"

# patterns that would indicate a geospatial inventory (not mere prose)
PATTERNS = [
    "latitude", "longitude", "coordinate", "gps", "survey number",
    "list of landslide", "inventory", "annexure", "ward no", "sl. no",
    "11°4", "11.4", "76.1", "76°1",
]
CONTEXT_PAT = re.compile(
    r"[^\n]{0,90}(latitude|longitude|coordinate|inventory|survey number|gps)[^\n]{0,90}",
    re.I)


def pdf_summary(name: str, reader: pypdf.PdfReader) -> dict:
    pages = [(pg.extract_text() or "") for pg in reader.pages]
    full = "\n".join(pages)
    low = full.lower()
    rec = {"document": name,
           "pages": len(pages),
           "extracted_chars": len(full),
           "first_300_chars": re.sub(r"\s+", " ", full[:300]),
           "pattern_counts": {p: low.count(p) for p in PATTERNS if low.count(p)},
           "context_samples": [re.sub(r"\s+", " ", m).strip()
                               for m in CONTEXT_PAT.findall(full)][:10]}
    return rec


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    import requests
    results = {"generated_utc": datetime.now(timezone.utc).isoformat(),
               "documents": []}
    for key, url in DOCS:
        rec = {"key": key, "url": url}
        try:
            r = requests.get(url, headers=HDR, timeout=120)
            rec["http_status"] = r.status_code
            rec["bytes"] = len(r.content)
            if r.status_code == 200:
                path = OUT / f"{key}.pdf"
                path.write_bytes(r.content)
                reader = pypdf.PdfReader(str(path))
                s = pdf_summary(key, reader)
                s["saved_as"] = str(path.relative_to(ROOT))
                rec.update(s)
            else:
                rec["note"] = r.text[:200]
        except Exception as exc:  # noqa: BLE001
            rec["error"] = f"{type(exc).__name__}: {exc}"
        results["documents"].append(rec)
        line = (f"{key}: HTTP {rec.get('http_status')} {rec.get('bytes')}B "
                f"pages={rec.get('pages')} chars={rec.get('extracted_chars')}"
                if "pages" in rec else f"{key}: FAIL {rec.get('error', rec.get('note'))}")
        print(line)

    # go_ms6 nature check
    rec = {"key": "ksdma_go_ms6_dmd_gsi", "path": str(GO_MS6.relative_to(ROOT))}
    try:
        reader = pypdf.PdfReader(str(GO_MS6))
        texts = [(pg.extract_text() or "") for pg in reader.pages]
        imgs = [len(pg.images) for pg in reader.pages]
        rec.update({"pages": len(texts),
                    "extracted_chars": sum(len(t) for t in texts),
                    "images_per_page": imgs,
                    "raw_text_preview": "".join(texts)[:200]})
    except Exception as exc:  # noqa: BLE001
        rec["error"] = f"{type(exc).__name__}: {exc}"
    results["documents"].append(rec)
    print("go_ms6:", rec.get("pages"), "pages,", rec.get("extracted_chars"),
          "chars, images/page:", rec.get("images_per_page"))

    (OUT / "ksdma_documents_assessment.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"evidence -> {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
