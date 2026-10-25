"""Acquire the 2018 Kerala monsoon landslide inventory (Hao/van Westen, DANS).

Source: doi:10.17026/dans-x6c-y7x2 — 4728 landslides statewide, CC-BY-4.0.
Wayanad subset is filtered later; the original statewide files are preserved unchanged.
"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from fetch import download

OUT = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\kerala_2018_dans")
OUT.mkdir(parents=True, exist_ok=True)

BASE = "https://phys-techsciences.datastations.nl/api/access/datafile/{fid}"
FILES = {
    6643: "easy-migration.zip",
    6575: "Kerela landslide.cpg",
    6579: "Kerela landslide.dbf",
    6649: "Kerela landslide.mid",
    6645: "Kerela landslide.mif",
    6578: "Kerela landslide.prj",
    6583: "Kerela landslide.sbn",
    6580: "Kerela landslide.sbx",
    6576: "Kerela landslide.shp",
    6581: "Kerela landslide.shx",
    6577: "Kerela landslide.xml",
    6650: "metadata.pdf",
}

for fid, name in FILES.items():
    download(BASE.format(fid=fid), OUT / name, min_bytes=1)

print("done")
for p in sorted(OUT.iterdir()):
    print(f"  {p.name:26s} {p.stat().st_size/1e3:9.1f} KB")
