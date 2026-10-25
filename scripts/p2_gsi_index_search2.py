"""Search all 1188 GSI reports for Wayanad regardless of the State field, and list
which candidate PDFs are already on disk."""
import json
import pathlib
import re

RAW = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gsi_bhusanket")
txt = (RAW / "LandslideReport.json").read_text(encoding="utf-8", errors="replace")
body = txt.split("=", 1)[1]
body = re.sub(r"^\s*LandslideReportData.*$", "", body, flags=re.M)
body = re.sub(r"//[^\n]*", "", body)
body = re.sub(r",(\s*[}\]])", r"\1", body)
recs = json.loads(body)

print("=== Any report (any state) whose title mentions Wayanad/Wynad ===")
n = 0
for r in recs:
    t = str(r.get("Title of the project", "")).upper()
    if "WAYANAD" in t or "WYNAD" in t:
        n += 1
        print(f"  {str(r.get('State')):14s} | {str(r.get('Field Season')):12s} | "
              f"{str(r.get('Type of project'))[:22]:22s} | acc={str(r.get('Acc. No.')):26s} | {t[:120]}")
print("count:", n)

print("\n=== Distinct State values (sanity check for blank/mis-spelled Kerala) ===")
print(sorted({str(r.get("State")) for r in recs}))

print("\n=== PDFs on disk ===")
pdf = RAW / "pdf"
for p in sorted(pdf.glob("*.pdf")):
    print(f"  {p.name:34s} {p.stat().st_size/1e6:8.2f} MB")

print("\n=== Text extracts on disk ===")
for p in sorted(pathlib.Path(r"C:\Major\data\interim\gsi_pdf_text").glob("*.txt")):
    print(f"  {p.name:38s} {p.stat().st_size:9d} B")
