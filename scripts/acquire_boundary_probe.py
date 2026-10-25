import json, pathlib, re, zipfile, sys
import requests
sys.path.insert(0, r"C:\Major\scripts")
from fetch import download

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
RAW = pathlib.Path(r"C:\Major\data\raw")

# --- GADM 4.1 India level 2 ---
z = download("https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IND_2.json.zip",
             RAW / "boundary" / "gadm41_IND_2.json.zip", min_bytes=100_000)
with zipfile.ZipFile(z) as zf:
    print("gadm contents:", zf.namelist())
    zf.extractall(RAW / "boundary" / "gadm41_IND_2")
print("extracted to", RAW / "boundary" / "gadm41_IND_2")

# --- Nominatim polygon for cross-check ---
try:
    r = requests.get("https://nominatim.openstreetmap.org/search",
                     params={"q": "Wayanad, Kerala, India", "format": "json",
                             "polygon_geojson": 1, "limit": 3},
                     headers=H, timeout=60)
    data = r.json()
    print("nominatim results:", [(d.get("display_name", "")[:70], d.get("type"), d.get("osm_type")) for d in data])
    keep = [d for d in data if d.get("geojson")]
    if keep:
        out = RAW / "boundary" / "osm_nominatim_wayanad.geojson"
        out.write_text(json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {k: d.get(k) for k in
              ("display_name", "osm_type", "osm_id", "class", "type", "boundingbox")},
             "geometry": d["geojson"]} for d in keep]}, indent=1), encoding="utf-8")
        print("wrote", out, out.stat().st_size)
except Exception as e:
    print("nominatim ERR", type(e).__name__, str(e)[:120])

# --- bhusanket portal links ---
try:
    r = requests.get("https://bhusanket.gsi.gov.in/statewiseLandslideReport.html", headers=H, timeout=60)
    links = re.findall(r'href=["\']([^"\']+)["\']', r.text)
    print("bhusanket links:", [l for l in links if any(k in l.lower() for k in ("pdf", "kerala", "report"))][:25])
except Exception as e:
    print("bhusanket ERR", str(e)[:100])

# --- GLiM on PANGAEA ---
for u in ["https://store.pangaea.de/Publications/Hartmann-etal_2012/glim_wgs84_0deg01.zip",
          "https://download.pangaea.de/dataset/788537/files/glim_wgs84_0deg01.zip"]:
    try:
        r = requests.head(u, headers=H, timeout=40, allow_redirects=True)
        print(f"glim {u[-45:]:45s} {r.status_code} len={r.headers.get('Content-Length')}")
    except Exception as e:
        print("glim ERR", u[-40:], str(e)[:60])

# --- ISRIC WCS coverages ---
try:
    r = requests.get("https://maps.isric.org/mapserv?map=/map/clay.map",
                     params={"SERVICE": "WCS", "VERSION": "2.0.1", "REQUEST": "GetCapabilities"},
                     headers=H, timeout=60)
    ids = re.findall(r"<wcs:CoverageId>([^<]+)</wcs:CoverageId>", r.text)
    print("isric clay coverages:", ids[:8], "total", len(ids))
except Exception as e:
    print("isric ERR", str(e)[:100])
