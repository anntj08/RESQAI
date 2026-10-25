"""Search the GSI Bhusanket report index for every Kerala report that could hold
Wayanad slide records or Wayanad susceptibility mapping.

Triggered by bibliography entries in the 2025 post-disaster report that point at
a 2019-2020 Wayanad/Kannur post-disaster report and 1:50,000 susceptibility
reports covering toposheets 58A/1,2,3,5,6,7,11.
"""
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

ker = [r for r in recs if str(r.get("State", "")).strip().lower() == "kerala"]
print(f"total reports={len(recs)}  kerala={len(ker)}")


def show(r, tag=""):
    print(f"  {tag}{str(r.get('Field Season')):12s} | {str(r.get('Type of project'))[:24]:24s} "
          f"| acc={str(r.get('Acc. No.')):24s} | {str(r.get('Title of the project'))[:150]}")


print("\n=== A. Kerala Post Disaster Studies, all seasons ===")
for r in sorted(ker, key=lambda x: str(x.get("Field Season"))):
    if "post" in str(r.get("Type of project", "")).lower():
        show(r)

print("\n=== B. Kerala reports mentioning Wayanad / Wynad anywhere in title ===")
for r in ker:
    t = str(r.get("Title of the project", "")).upper()
    if "WAYANAD" in t or "WYNAD" in t:
        show(r)

print("\n=== C. Kerala reports mentioning toposheets 58A or 49M ===")
for r in ker:
    t = str(r.get("Title of the project", "")).upper()
    if re.search(r"\b58\s?A\b|\b49\s?M\b", t):
        show(r)

print("\n=== D. Kerala landslide susceptibility mapping reports (all areas) ===")
for r in ker:
    t = str(r.get("Title of the project", "")).lower()
    if "susceptibility" in t:
        show(r)

print("\n=== E. Fuzzy: any report title containing kannur (2019-20 report covers Wayanad+Kannur) ===")
for r in ker:
    t = str(r.get("Title of the project", "")).upper()
    if "KANNUR" in t or "CALICUT" in t or "KOZHIKODE" in t:
        show(r)
