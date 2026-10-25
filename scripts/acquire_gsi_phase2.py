"""Phase 2: acquire additional GSI Kerala reports that cover Wayanad (post-2018 gap)."""
import pathlib
import sys
import urllib.parse

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

OUT = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gsi_bhusanket\pdf")
BASE = "https://bhusanket.gsi.gov.in/Output/LandslideReport/"

ITEMS = [
    ("Kerala", "Post Disaster Studies", "PDLS_2024_51817", "gsi_PDLS_2024_51817"),
    ("Kerala", "Post Disaster Studies", "PDLS_2025_61074", "gsi_PDLS_2025_61074"),
    ("Kerala", "Post Disaster Studies", "14115", "gsi_14115"),
    ("Kerala", "Post Disaster Studies", "14336", "gsi_14336"),
    ("Kerala", "Macro scale studies", "12272", "gsi_12272"),
    ("Kerala", "Macro scale studies", "12236", "gsi_12236"),
]

for st, pt, acc, stem in ITEMS:
    url = BASE + "/".join(urllib.parse.quote(x, safe="") for x in (st, pt, acc)) + ".pdf"
    try:
        download(url, OUT / f"{stem}.pdf", min_bytes=200_000)
    except Exception as e:
        print(f"FAILED {stem}: {type(e).__name__} {str(e)[:120]}")
