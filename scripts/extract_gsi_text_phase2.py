"""Extract text from newly acquired GSI PDFs (phase 2)."""
import logging
import pathlib
import warnings

import pypdf

logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

PDF = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gsi_bhusanket\pdf")
OUT = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")
OUT.mkdir(parents=True, exist_ok=True)

NEW = ["gsi_PDLS_2024_51817", "gsi_PDLS_2025_61074", "gsi_14115",
       "gsi_14336", "gsi_12272", "gsi_12236"]

for stem in NEW:
    p = PDF / f"{stem}.pdf"
    if not p.exists():
        print(f"{stem:26s} MISSING")
        continue
    try:
        r = pypdf.PdfReader(str(p))
        texts = [(pg.extract_text() or "") for pg in r.pages]
        total = sum(len(t) for t in texts)
        (OUT / f"{stem}.txt").write_text(
            "\n\n".join(f"===== PAGE {i+1} =====\n{t}" for i, t in enumerate(texts)),
            encoding="utf-8")
        hits = [i + 1 for i, t in enumerate(texts) if "wayanad" in t.lower()]
        print(f"{stem:26s} pages={len(texts):3d} chars={total:7d} wayanad_pages={hits[:20]}")
    except Exception as e:
        print(f"{stem:26s} ERR {type(e).__name__} {str(e)[:80]}")
