"""Independent locality check for July 2024 event place names via OSM/Nominatim."""
import json
import time

import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use; contact: student project)"}
OUT = r"C:\Major\data\interim\locality_checks_osm.json"

NAMES = ["Mundakkai, Wayanad, Kerala", "Chooralmala, Wayanad, Kerala",
         "Meppadi, Wayanad, Kerala", "Puthumala, Wayanad, Kerala",
         "Vellarimala, Wayanad, Kerala", "Attamala, Wayanad, Kerala",
         "Punjirimattom, Wayanad, Kerala", "Kottapadi, Wayanad, Kerala",
         "Muppainadu, Wayanad, Kerala", "Nellimala, Wayanad, Kerala"]

res = {}
for q in NAMES:
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": q, "format": "json", "limit": 3},
                         headers=H, timeout=45)
        d = r.json()
        res[q] = d
        if d:
            for hit in d:
                print(f"{q:36s} -> {hit.get('lat'):>10} {hit.get('lon'):>10} "
                      f"[{hit.get('type')}] {hit.get('display_name','')[:60]}")
        else:
            print(f"{q:36s} -> no result")
    except Exception as e:
        print(f"{q:36s} ERR {type(e).__name__} {str(e)[:60]}")
    time.sleep(1.2)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(res, f, indent=1)
print("wrote", OUT)
