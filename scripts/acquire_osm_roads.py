"""Optional layer: OSM road network for Wayanad (distance-to-road predictor)."""
import json, pathlib
import geopandas as gpd
import requests
from shapely.geometry import LineString

H = {"User-Agent": "RESQAI-research/1.0 (academic use)"}
RAW = pathlib.Path(r"C:\Major\data\raw")
PROC = pathlib.Path(r"C:\Major\data\processed")

q = """
[out:json][timeout:180];
way["highway"](11.42,75.75,11.99,76.46);
out geom tags;
"""
r = requests.post("https://overpass-api.de/api/interpreter", data={"data": q}, headers=H, timeout=300)
r.raise_for_status()
data = r.json()
print("OSM elements:", len(data.get("elements", [])))

feats = []
for el in data["elements"]:
    geom = el.get("geometry")
    if not geom or len(geom) < 2:
        continue
    feats.append({
        "type": "Feature",
        "properties": {k: v for k, v in el.get("tags", {}).items() if k in ("highway", "name", "surface", "ref")},
        "geometry": {"type": "LineString", "coordinates": [[p["lon"], p["lat"]] for p in geom]},
    })
gj = {"type": "FeatureCollection", "features": feats}
out_raw = RAW / "additional" / "osm_roads_wayanad.geojson"
out_raw.parent.mkdir(parents=True, exist_ok=True)
out_raw.write_text(json.dumps(gj), encoding="utf-8")
print("raw roads:", len(feats))

g = gpd.read_file(RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
way = g[g["NAME_2"] == "Wayanad"]
roads = gpd.read_file(out_raw)
clip = gpd.clip(roads, way)
print("roads in district:", len(clip), "| length km:", round(clip.to_crs(32643).length.sum() / 1000, 1))
print(clip.highway.value_counts().head(8).to_string())
out = PROC / "additional" / "osm_roads_wayanad_clip.gpkg"
out.parent.mkdir(parents=True, exist_ok=True)
clip.to_file(out, driver="GPKG")
print("wrote", out)
