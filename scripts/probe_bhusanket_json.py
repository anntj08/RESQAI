import json, pathlib, re
import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
RAW = pathlib.Path(r"C:\Major\data\raw")

for path in ["json/LandslideReport/LandslideReport.json", "json/config.json"]:
    url = "https://bhusanket.gsi.gov.in/" + path
    r = requests.get(url, headers=H, timeout=60)
    print(f"\n=== {path} {r.status_code} {len(r.content)} bytes")
    if r.status_code == 200:
        (RAW / "landslide_inventory" / "gsi_bhusanket").mkdir(parents=True, exist_ok=True)
        out = RAW / "landslide_inventory" / "gsi_bhusanket" / path.split("/")[-1]
        out.write_bytes(r.content)
        try:
            data = r.json()
            s = json.dumps(data, indent=1)
            print(s[:1500])
        except Exception:
            print(r.text[:600])
