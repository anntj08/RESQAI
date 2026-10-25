"""Targeted scan of the remaining phase-2 documents for Wayanad event records.

1. GSI 15990 — Plamoola subsidence (2020-21): is it a landslide, what date/coords?
2. KSDMA Meppadi PDNA 2024 (647 pp) — any tabulated landslide inventory or
   coordinate lists, plus the damage/impact figures for the July 2024 event.
3. KSDMA Memorandum 2024 — district/local-body impact figures.
"""
import pathlib
import re

BASE = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")


def load(stem):
    t = (BASE / f"{stem}.txt").read_text(encoding="utf-8")
    p = re.split(r"===== PAGE (\d+) =====", t)
    return {int(p[i]): p[i + 1] for i in range(1, len(p), 2)}


print("=" * 70)
print("GSI 15990  PLAMOOLA SUBSIDENCE, WAYANAD")
pgs = load("gsi_15990")
print("pages:", len(pgs))
for n in sorted(pgs)[:6]:
    body = re.sub(r"\s+", " ", pgs[n]).strip()
    if body:
        print(f"\n--- p{n}: {body[:1100]}")

# coordinate patterns anywhere in 15990
full = "\n".join(pgs[n] for n in sorted(pgs))
print("\ncoordinate-like strings in 15990:")
for m in set(re.findall(r"\d{1,2}\s*[°˚]\s*\d{1,2}\s*['\u2019]\s*\d{1,2}(?:\.\d+)?\s*[\"\u201d]\s*[NS]?", full)):
    print("   ", m)
for kw in ("subsidence", "landslide", "sinking", "2020", "2021"):
    hits = [n for n, b in pgs.items() if kw.lower() in b.lower()]
    print(f"  '{kw}': pages {hits[:12]}")

print("\n" + "=" * 70)
print("KSDMA Meppadi PDNA 2024")
pgs = load("ksdma_meppadi_pdna_2024")
print("pages:", len(pgs))
coord = {}
for n, b in pgs.items():
    if re.search(r"\d{1,2}\s*[°˚]\s*\d{1,2}\s*['\u2019]", b):
        coord[n] = re.findall(r"\d{1,2}\s*[°˚]\s*\d{1,2}\s*['\u2019]\s*\d{1,2}(?:\.\d+)?\s*[\"\u201d]\s*[NS]",
                              b)
print("pages with DMS coordinates:", list(coord)[:25])
for n in list(coord)[:6]:
    print(f"   p{n}: {coord[n][:4]}")

for kw in ("Mundakkai", "Chooralmala", "Attamala", "Vellarimala", "Punjirimattom"):
    hits = [n for n, b in pgs.items() if kw.lower() in b.lower()]
    print(f"  '{kw}': {len(hits)} pages, first {hits[:8]}")

print("\n" + "=" * 70)
print("KSDMA Memorandum 2024")
pgs = load("ksdma_memorandum_17082024")
print("pages:", len(pgs))
for n in sorted(pgs):
    b = re.sub(r"\s+", " ", pgs[n])
    if re.search(r"(?i)wayanad", b) and re.search(r"(?i)landslide|death|casualt|damage", b):
        print(f"\n--- p{n}: {b[:900]}")
