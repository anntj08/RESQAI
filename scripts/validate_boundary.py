import json
import pathlib

import geopandas as gpd
import pandas as pd

RAW = pathlib.Path(r"C:\Major\data\raw")

# --- GADM level 2 ---
gadm_path = RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json"
g = gpd.read_file(gadm_path)
print("GADM IND level2 features:", len(g), "| cols:", [c for c in g.columns][:12])
cand = g[g["NAME_2"].astype(str).str.contains("Wayanad", case=False, na=False)]
print("Wayanad matches:", len(cand), cand[["NAME_1", "NAME_2", "TYPE_2"]].to_dict("records"))
way = cand.to_crs(32643)  # UTM 43N for area
print("area km2 (UTM43N):", round(way.area.sum() / 1e6, 1))
print("bounds WGS84:", tuple(round(v, 4) for v in cand.total_bounds))
print("geometry types:", cand.geometry.geom_type.tolist(), "| valid:", cand.geometry.is_valid.tolist())

# --- OSM / Nominatim ---
osm = gpd.read_file(RAW / "boundary" / "osm_nominatim_wayanad.geojson")
print("\nOSM features:", len(osm), osm[["osm_type", "class", "type"]].to_dict("records"))
print("OSM bounds:", tuple(round(v, 4) for v in osm.total_bounds))
print("OSM area km2 (UTM43N):", round(osm.to_crs(32643).area.sum() / 1e6, 1))

# --- coverage check against acquired DEM tiles ---
import rasterio
minx, miny, maxx, maxy = cand.total_bounds
print(f"\nWayanad bbox: {minx:.4f},{miny:.4f},{maxx:.4f},{maxy:.4f}")
tiles = sorted((RAW / "dem" / "copernicus_glo30").glob("*.tif"))
covered = []
for t in tiles:
    with rasterio.open(t) as ds:
        b = ds.bounds
        inter = not (b.right < minx or b.left > maxx or b.top < miny or b.bottom > maxy)
        print(f"  {t.name}: {b.left:.2f}-{b.right:.2f}E {b.bottom:.2f}-{b.top:.2f}N intersects={inter}")
        if inter:
            covered.append(b)

# union coverage test at boundary vertices
from shapely.geometry import Point, box
from shapely.ops import unary_union
u = unary_union([box(b.left, b.bottom, b.right, b.top) for b in covered])
pts = [Point(x, y) for x, y in __import__("numpy").vstack([cand.geometry.iloc[0].exterior.coords])]
outside = [p for p in pts if not u.contains(p)]
print(f"district boundary vertices outside DEM union: {len(outside)} / {len(pts)}")

osm_w = osm.to_crs(4326)
diff_note = ""
u2 = unary_union([box(b.left, b.bottom, b.right, b.top) for b in covered])
o_out = [Point(x, y) for x, y in __import__("numpy").vstack([osm_w.geometry.iloc[0].exterior.coords]) if not u2.contains(Point(x, y))]
print(f"OSM boundary vertices outside DEM union: {len(o_out)} / {len(list(osm_w.geometry.iloc[0].exterior.coords))}")
