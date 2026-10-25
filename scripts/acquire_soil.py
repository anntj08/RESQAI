"""ISRIC SoilGrids 250m via WCS, Wayanad window (75.60-76.55E, 11.25-12.00N)."""
import pathlib
import re
import sys

import requests

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
OUT = pathlib.Path(r"C:\Major\data\raw\soil\soilgrids250m")
OUT.mkdir(parents=True, exist_ok=True)

BBOX = (75.60, 11.25, 76.55, 12.00)
props = {
    "clay": "clay", "sand": "sand", "silt": "silt",
    "bdod": "bdod", "soc": "soc", "cec": "cec", "cfvo": "cfvo",
}
depths = ["0-5cm", "15-30cm"]

for prop in props:
    mapfile = f"/map/{prop}.map"
    for depth in depths:
        cov = f"{prop}_{depth}_mean"
        dest = OUT / f"soilgrids_{prop}_{depth}_mean_wayanad.tif"
        if dest.exists() and dest.stat().st_size > 5000:
            print("SKIP", dest.name)
            continue
        params = {
            "map": mapfile, "SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": "GetCoverage",
            "COVERAGEID": cov, "FORMAT": "GEOTIFF_INT16",
            "SUBSET": [f"Long({BBOX[0]},{BBOX[2]})", f"Lat({BBOX[1]},{BBOX[3]})"],
            "SUBSETTINGCRS": "http://www.opengis.net/def/crs/EPSG/0/4326",
            "OUTPUTCRS": "http://www.opengis.net/def/crs/EPSG/0/4326",
        }
        try:
            r = requests.get("https://maps.isric.org/mapserv", params=params, headers=H, timeout=180)
            ctype = r.headers.get("Content-Type", "")
            if r.status_code == 200 and ("tiff" in ctype.lower() or r.content[:2] in (b"II", b"MM")):
                dest.write_bytes(r.content)
                print(f"OK {dest.name} {len(r.content)/1e3:.0f} KB")
            else:
                print(f"FAIL {cov} status={r.status_code} ct={ctype[:40]} body={r.text[:160]}")
        except Exception as e:
            print(f"ERR {cov} {type(e).__name__} {str(e)[:100]}")
