"""Print full titles of candidate GSI Kerala reports relevant to Wayanad."""
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

WANT = ["14115", "14336", "12272", "12236", "PDLS_2024_51817", "PDLS_2025_61074",
        "14998", "15000", "15178", "15179", "15180", "15181", "15182",
        "15740", "15741", "15742", "14252", "14253", "15990", "14769"]

for acc in WANT:
    hit = [r for r in recs if str(r.get("Acc. No.")).strip() == acc]
    if not hit:
        print(f"{acc}: NOT FOUND")
        continue
    r = hit[0]
    print(f"\nacc={acc} | season={r.get('Field Season')} | type={r.get('Type of project')}")
    print(f"  {r.get('Title of the project')}")

# also: any Kerala report whose title mentions a Wayanad toposheet prefix
print("\n\n=== Kerala reports referencing Wayanad toposheets 58A / 49M ===")
for r in recs:
    if str(r.get("State", "")).strip().lower() != "kerala":
        continue
    t = str(r.get("Title of the project", "")).upper()
    if re.search(r"\b(58A|49M)\b", t) or "WYN" in t or "WAYANAD" in t:
        print(f"  {r.get('Field Season')} | {r.get('Acc. No.')} | {r.get('Type of project')} | {t[:130]}")
