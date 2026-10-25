import pathlib, sys, urllib.parse
sys.path.insert(0, r"C:\Major\scripts")
from fetch import download

OUT = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gsi_bhusanket\pdf")
BASE = "https://bhusanket.gsi.gov.in/Output/LandslideReport/"
items = [
    ("Kerala", "Macro scale studies", "14337"),
    ("Kerala", "Macro scale studies", "14767"),
    ("Kerala", "Macro scale studies", "14768"),
    ("Kerala", "Macro scale studies", "14999"),
    ("Kerala", "Post Disaster Studies", "ADDL. ITEM(LANDSLIDES OCCURRED IN JUNE 2018 AT WAYANAD DISTRICT, KERALA)"),
    ("Kerala", "Site Specific Studies", "14252"),
    ("Kerala", "Site Specific Studies", "14253"),
    ("Kerala", "Site Specific Studies", "15990"),
]
for st, pt, acc in items:
    url = BASE + "/".join(urllib.parse.quote(x, safe="") for x in (st, pt, acc)) + ".pdf"
    safe = acc.replace("ADDL. ITEM(LANDSLIDES OCCURRED IN JUNE 2018 AT WAYANAD DISTRICT, KERALA)", "2018_post_disaster_wayanad")
    download(url, OUT / f"gsi_{safe}.pdf", min_bytes=500_000)
print("done")
