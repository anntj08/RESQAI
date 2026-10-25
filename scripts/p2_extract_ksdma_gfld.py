"""Extract text from the KSDMA PDFs and acquire the GFLD supplementary tables."""
import logging
import pathlib
import sys
import warnings

import pypdf
import requests

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

logging.getLogger("pypdf").setLevel(logging.ERROR)
warnings.filterwarnings("ignore")

RAW = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\ksdma")
TXT = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")  # same convention: one .txt per pdf
TXT.mkdir(parents=True, exist_ok=True)

for p in sorted(RAW.glob("*.pdf")):
    try:
        r = pypdf.PdfReader(str(p))
        texts = [(pg.extract_text() or "") for pg in r.pages]
        total = sum(len(t) for t in texts)
        out = TXT / (p.stem + ".txt")
        out.write_text("\n\n".join(f"===== PAGE {i+1} =====\n{t}" for i, t in enumerate(texts)),
                       encoding="utf-8")
        wy = [i + 1 for i, t in enumerate(texts) if "wayanad" in t.lower()]
        print(f"{p.name:44s} pages={len(texts):3d} chars={total:7d} wayanad_pages={wy[:15]}")
    except Exception as e:
        print(f"{p.name:44s} ERR {type(e).__name__} {str(e)[:70]}")

print("\n--- GFLD supplementary tables (Froude & Petley 2018) ---")
GF = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gfld")
GF.mkdir(parents=True, exist_ok=True)
BASE = "https://nhess.copernicus.org/articles/18/2161/2018/"
for n in ("t01", "t02", "t03"):
    url = f"{BASE}nhess-18-2161-2018-{n}.xlsx"
    try:
        download(url, GF / f"nhess-18-2161-2018-{n}.xlsx", min_bytes=5_000)
    except Exception as e:
        print(f"FAILED {n}: {type(e).__name__} {str(e)[:110]}")
