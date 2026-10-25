import json, pathlib, re
import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
RAW = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\gsi_bhusanket")

txt = (RAW / "LandslideReport.json").read_text(encoding="utf-8", errors="replace")
body = txt.split("=", 1)[1].strip().rstrip(";")
body = re.sub(r"^\s*LandslideReportData.*$", "", body, flags=re.M)
body = re.sub(r"//[^\n]*", "", body)              # strip // comments
body = re.sub(r",(\s*[}\]])", r"\1", body)        # trailing commas
recs = json.loads(body)
print("total GSI reports:", len(recs))
print("keys:", list(recs[0].keys()))

wl = [r for r in recs if "wayanad" in json.dumps(r).lower()]
print(f"\n=== records mentioning Wayanad: {len(wl)}")
for r in wl:
    print(f"  acc={r.get('Acc. No.')} | {r.get('Field Season')} | {r.get('Type of project')} | {r.get('Title of the project')[:160]}")

for acc in ["14337", "14768", "14767"]:
    hit = [r for r in recs if str(r.get("Acc. No.")) == acc]
    print(f"\nacc {acc}:", json.dumps(hit[0], indent=1) if hit else "NOT FOUND")

js = requests.get("https://bhusanket.gsi.gov.in/js/statewiseLandslideReport.js", headers=H, timeout=60).text
(RAW / "statewiseLandslideReport.js").write_text(js, encoding="utf-8")
print("\n=== lines with pdf/open/href ===")
for line in js.splitlines():
    if any(k in line for k in ("window.open", "href", ".pdf", "location", "Acc")):
        print(" ", line.strip()[:220])
