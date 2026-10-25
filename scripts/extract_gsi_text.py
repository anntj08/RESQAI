import logging
import pathlib
import warnings

import pypdf

logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

PDF = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gsi_bhusanket\pdf")
OUT = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")
OUT.mkdir(parents=True, exist_ok=True)

for p in sorted(PDF.glob("*.pdf")):
    try:
        r = pypdf.PdfReader(str(p))
        texts = [(pg.extract_text() or "") for pg in r.pages]
        total = sum(len(t) for t in texts)
        hits = [i + 1 for i, t in enumerate(texts)
                if ("latitude" in t.lower() and "longitude" in t.lower())]
        (OUT / (p.stem + ".txt")).write_text(
            "\n\n".join(f"===== PAGE {i+1} =====\n{t}" for i, t in enumerate(texts)), encoding="utf-8")
        print(f"{p.name:40s} pages={len(texts):3d} chars={total:7d} coord_pages={hits[:14]}")
    except Exception as e:
        print(f"{p.name:40s} ERR {type(e).__name__} {str(e)[:70]}")
