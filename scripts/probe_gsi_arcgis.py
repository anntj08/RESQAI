import json, pathlib, urllib.parse
import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
BASE = "https://bhusanket.gsi.gov.in/gisserver/rest/services"

r = requests.get(f"{BASE}?f=json", headers=H, timeout=60)
print("services status", r.status_code)
try:
    svcs = r.json().get("services", [])
    print("service count:", len(svcs))
    for s in svcs:
        print("  ", s.get("name"), s.get("type"))
except Exception:
    print(r.text[:500])

# national landslide point layer
u = f"{BASE}/Hosted/India_All_Landslided/FeatureServer/0"
r = requests.get(u, params={"f": "json"}, headers=H, timeout=60)
print("\nlayer meta status", r.status_code, len(r.text))
try:
    m = r.json()
    print("name:", m.get("name"), "| geometry:", m.get("geometryType"))
    print("fields:", [(f["name"], f["type"]) for f in m.get("fields", [])])
    print("count:", requests.get(u + "/query", params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
                                  headers=H, timeout=90).json())
except Exception as e:
    print("parse err", e, r.text[:300])
