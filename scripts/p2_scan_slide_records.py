"""Scan phase-2 GSI reports for slide records (Slide No. / Latitude / Longitude)."""
import pathlib
import re

BASE = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")

for stem in ["gsi_PDLS_2024_51817", "gsi_PDLS_2025_61074", "gsi_14115"]:
    t = (BASE / f"{stem}.txt").read_text(encoding="utf-8")
    p = re.split(r"===== PAGE (\d+) =====", t)
    pgs = {int(p[i]): p[i + 1] for i in range(1, len(p), 2)}
    full = "\n".join(pgs[n] for n in sorted(pgs))

    print(f"\n\n================ {stem} ================")
    slides = re.findall(r"Slide No\.?\s*:?\s*([A-Z0-9][^\n]{0,45})", full)
    print(f"'Slide No.' occurrences: {len(slides)}")
    for s in slides:
        print("   ", s.strip()[:60])

    print("\nKER/WYD mentions:", len(re.findall(r"KER/WYD", full)))
    # page map for Wayanad
    wyp = [n for n, txt in pgs.items() if "wayanad" in txt.lower()]
    print("Wayanad pages:", wyp)

    # toposheet mentions
    tops = sorted(set(re.findall(r"58\s?A\s?/\s?\d{1,2}", full)))
    print("toposheets seen:", tops[:20])
