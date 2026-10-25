import pathlib, re, sys

BASE = pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text")
out = []

def pages(f):
    t = (BASE / f"{f}.txt").read_text(encoding="utf-8")
    p = re.split(r"===== PAGE (\d+) =====", t)
    return {int(p[i]): p[i + 1] for i in range(1, len(p), 2)}

checks = {
    "gsi_14768": [26, 27, 28],
    "gsi_14999": [23, 24],
    "gsi_14767": [30, 33],
}
for f, ns in checks.items():
    pg = pages(f)
    for n in ns:
        txt = pg.get(n, "")
        out.append(f"\n\n########## {f} page {n} (len {len(txt)}) ##########\n")
        out.append(txt[:2600])

pathlib.Path(r"C:\Major\data\interim\table_review.txt").write_text("\n".join(out), encoding="utf-8")
print("written")
