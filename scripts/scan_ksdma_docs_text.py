"""Deep text scan of the two KSDMA 2024-review PDFs saved by
assess_ksdma_2024_documents.py, with full-match context and Malayalam patterns.

RUN-2026-10-29-09 evidence step (read-only over the saved evidence PDFs).
Decides report-vs-inventory classification evidence:
  * English patterns: latitude, longitude, coordinate(s), GPS, survey number,
    list of landslides, inventory, annexure, ward no.
  * Malayalam patterns: latitude / longitude / list / survey number /
    ward / inventory / coordinate.
  * per-page character counts and image counts (image-only pages hide tables).
"""
from __future__ import annotations

import json
import pathlib
import re
import sys
from datetime import datetime, timezone

import pypdf

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "interim" / "inventory_source_review_2026-10-29"

DOCS = ["ksdma_fps2025_srh_needs", "ksdma_environment_committee_13th_report"]

EN_PAT = re.compile(
    r"[^\n]{0,80}(latitude|longitude|coordinates?|gps|survey number|"
    r"list of landslides|inventory|annexure|ward no)[^\n]{0,80}", re.I)
ML_PAT = re.compile(
    r"[^\n]{0,80}(അക്ഷാംശം|രേഖാംശം|സർവേ നമ്പർ|വാർഡ്|ഇൻവെന്ററി|പട്ടിക)[^\n]{0,80}")
SLNO_PAT = re.compile(r"[^\n]{0,60}(Sl\.?\s*No|S\.?\s*No|ക്ര\.?നം)[^\n]{0,60}")


def main() -> int:
    results = {"generated_utc": datetime.now(timezone.utc).isoformat(), "documents": []}
    for key in DOCS:
        path = OUT / f"{key}.pdf"
        reader = pypdf.PdfReader(str(path))
        pages = [(pg.extract_text() or "") for pg in reader.pages]
        imgs = [len(pg.images) for pg in reader.pages]
        full = "\n".join(pages)
        rec = {
            "document": key,
            "pages": len(pages),
            "chars_total": len(full),
            "chars_per_page_first12": [len(t) for t in pages[:12]],
            "images_per_page_first12": imgs[:12],
            "image_only_pages": [i + 1 for i, (t, n) in enumerate(zip(pages, imgs))
                                 if len(t) < 40 and n > 0][:20],
            "en_contexts": [re.sub(r"\s+", " ", m).strip() for m in EN_PAT.findall(full)][:12],
            "ml_contexts": [re.sub(r"\s+", " ", m).strip() for m in ML_PAT.findall(full)][:12],
            "slno_contexts": [re.sub(r"\s+", " ", m).strip()
                              for m in SLNO_PAT.findall(full)][:10],
        }
        rec["en_counts"] = {p: full.lower().count(p) for p in
                            ("latitude", "longitude", "coordinate", "gps",
                             "survey number", "inventory", "annexure")}
        results["documents"].append(rec)
        print(f"== {key}: pages={rec['pages']} chars={rec['chars_total']} "
              f"image_only_pages={rec['image_only_pages']}")
        print("   en_counts:", rec["en_counts"])
        print("   ml/slno hits:", len(rec["ml_contexts"]), "/", len(rec["slno_contexts"]))
        for c in rec["en_contexts"][:8]:
            print("   EN:", c[:160])
        for c in rec["ml_contexts"][:8]:
            print("   ML:", c[:160])
        for c in rec["slno_contexts"][:6]:
            print("   SN:", c[:160])

    (OUT / "ksdma_documents_deepscan.json").write_text(
        json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("evidence ->", OUT.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
