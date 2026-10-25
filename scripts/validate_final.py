import glob, hashlib, json, pathlib
import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
from rasterio.windows import from_bounds

RAW = pathlib.Path(r"C:\Major\data\raw")
PROC = pathlib.Path(r"C:\Major\data\processed")
INT = pathlib.Path(r"C:\Major\data\interim")

g = gpd.read_file(RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
way = g[g["NAME_2"] == "Wayanad"]

# --- WorldCover classes in Wayanad ---
wc = next((RAW / "landcover").glob("*.tif"))
with rasterio.open(wc) as ds:
    win = from_bounds(75.60, 11.25, 76.55, 12.00, ds.transform)
    a = ds.read(1, window=win)
    transform = ds.window_transform(win)
    from rasterio.features import geometry_mask
    mask = geometry_mask([way.geometry.iloc[0]], out_shape=a.shape, transform=transform, invert=True)
    vals, counts = np.unique(a[mask], return_counts=True)
print("WorldCover classes in Wayanad (code, pixels, %):")
tot = counts.sum()
for v, c in sorted(zip(vals, counts), key=lambda x: -x[1])[:8]:
    print(f"  {int(v):3d}  {c:9d}  {100*c/tot:5.2f}%")
print("  (0 = nodata per product metadata)")

# --- inventory points inside district ---
files = {
    "14337": INT / "inventory_extracts" / "inventory_14337_wayanad.csv",
    "14768_t4": INT / "inventory_extracts" / "inventory_14768_table4.csv",
    "14768_t5": INT / "inventory_extracts" / "inventory_14768_table5.csv",
    "2018": INT / "inventory_extracts" / "inventory_2018_postdisaster.csv",
}
print("\nInventory points inside GADM Wayanad polygon:")
for k, f in files.items():
    d = pd.read_csv(f)
    pts = gpd.GeoDataFrame(d, geometry=gpd.points_from_xy(d.longitude_dd, d.latitude_dd), crs=4326)
    inside = pts.within(way.geometry.iloc[0]).sum()
    print(f"  {k:10s} {inside}/{len(d)} inside  (lat {d.latitude_dd.min():.3f}-{d.latitude_dd.max():.3f})")

# --- processed outputs ---
print("\nProcessed files:")
for p in sorted(PROC.rglob("*")):
    if p.is_file():
        print(f"  {p.relative_to(PROC.parent.parent)}  {p.stat().st_size/1e6:.2f} MB")
