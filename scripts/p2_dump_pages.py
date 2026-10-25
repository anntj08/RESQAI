"""Dump selected pages from a phase-2 GSI text extract for review."""
import pathlib
import re
import sys

BASE = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")
stem = sys.argv[1]
pages = [int(x) for x in sys.argv[2].split(",")]

t = (BASE / f"{stem}.txt").read_text(encoding="utf-8")
p = re.split(r"===== PAGE (\d+) =====", t)
pgs = {int(p[i]): p[i + 1] for i in range(1, len(p), 2)}

for n in pages:
    print(f"\n########## {stem} page {n} ##########")
    print(pgs.get(n, "(missing)")[:3000])
