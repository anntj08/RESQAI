import pathlib
import geopandas as gpd
import numpy as np
import pandas as pd

INT = pathlib.Path(r"C:\Major\data\interim\inventory_extracts")
src = {
    "14337": "inventory_14337_wayanad.csv",
    "14768_t4": "inventory_14768_table4.csv",
    "14768_t5": "inventory_14768_table5.csv",
    "2018": "inventory_2018_postdisaster.csv",
}
g = {}
for k, f in src.items():
    d = pd.read_csv(INT / f)
    g[k] = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.longitude_dd, d.latitude_dd), crs=4326).to_crs(32643)

def near(a, b, tol):
    hit = 0
    for geom in g[a].geometry:
        if g[b].distance(geom).min() <= tol:
            hit += 1
    return hit

print("candidate duplicate counts (same event recorded in two sources):")
for a, b in [("14768_t4", "14337"), ("14768_t5", "14337"), ("14768_t5", "14768_t4"), ("2018", "14337")]:
    for tol in (500, 1000):
        print(f"  {a:9s} within {tol:4d} m of {b:8s}: {near(a, b, tol)}/{len(g[a])}")

# spatial spread of each source
print("\nsource footprints (bbox):")
for k, gg in g.items():
    b = gg.total_bounds
    print(f"  {k:9s} n={len(gg):3d}  {b[0]:.0f},{b[1]:.0f} -> {b[2]:.0f},{b[3]:.0f} (UTM43N)")
