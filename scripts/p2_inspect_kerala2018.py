"""Inspect the 2018 Kerala inventory and extract the Wayanad subset."""
import pathlib

import geopandas as gpd
import pandas as pd

RAW = pathlib.Path(r"C:\Major\data\raw\landslide_inventory\kerala_2018_dans")
shp = RAW / "Kerela landslide.shp"

g = gpd.read_file(shp)
print("features:", len(g))
print("crs:", g.crs)
print("geometry types:", g.geom_type.value_counts().to_dict())
print("columns:", list(g.columns))
print("\nbounds:", tuple(round(v, 4) for v in g.total_bounds))

for c in g.columns:
    if c == "geometry":
        continue
    u = g[c].dropna().unique()
    if len(u) <= 25:
        print(f"\n{c} ({len(u)} unique): {list(u)}")
    else:
        print(f"\n{c}: {len(u)} unique, sample={list(u[:4])}")

# district field
dist_cols = [c for c in g.columns if "dist" in c.lower()]
print("\ndistrict-like columns:", dist_cols)
