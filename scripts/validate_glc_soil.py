import pathlib
import glob
import numpy as np
import pandas as pd
import rasterio

RAW = pathlib.Path(r"C:\Major\data\raw")

# ---------- NASA Global Landslide Catalog ----------
p = RAW / "landslide_inventory" / "nasa_glc" / "Global_Landslide_Catalog_Export_rows.csv"
glc = pd.read_csv(p, low_memory=False)
print("GLC total rows:", len(glc))
print("columns:", [c for c in glc.columns][:20])

glc["latitude"] = pd.to_numeric(glc["latitude"], errors="coerce")
glc["longitude"] = pd.to_numeric(glc["longitude"], errors="coerce")
box = glc[(glc.longitude.between(75.5, 76.6)) & (glc.latitude.between(11.2, 12.1))]
print(f"\nGLC records in Wayanad bbox: {len(box)}")
kerala = glc[glc.get("admin_division_name", "").astype(str).str.contains("Kerala", case=False, na=False)] \
    if "admin_division_name" in glc.columns else pd.DataFrame()
print(f"GLC records tagged Kerala: {len(kerala)}")
cols = [c for c in ["event_id", "event_date", "event_title", "landslide_category", "latitude", "longitude",
                    "location_description", "admin_division_name", "location_accuracy", "fatalities"] if c in glc.columns]
print(box[cols].to_string(index=False) if len(box) else "  (none)")
print("\nGLC date range:", glc["event_date"].astype(str).min(), "to", glc["event_date"].astype(str).max())
if len(box):
    box.to_csv(r"C:\Major\data\interim\inventory_extracts\nasa_glc_wayanad_bbox.csv", index=False)

# ---------- SoilGrids ----------
print("\n---------- SoilGrids ----------")
files = sorted(glob.glob(str(RAW / "soil" / "soilgrids250m" / "*.tif")))
print(f"{len(files)} files")
for f in files[:3]:
    with rasterio.open(f) as ds:
        a = ds.read(1)
        v = a[a != ds.nodata] if ds.nodata is not None else a
        print(f"{pathlib.Path(f).name}: {ds.width}x{ds.height} {ds.dtypes[0]} {ds.crs} res={ds.res} "
              f"bounds={tuple(round(x,3) for x in ds.bounds)} nodata={ds.nodata} "
              f"min={v.min()} max={v.max()}")
allr = []
for f in files:
    with rasterio.open(f) as ds:
        allr.append((pathlib.Path(f).name, ds.width, ds.height, ds.crs.to_string() if ds.crs else None,
                     round(ds.res[0], 6), tuple(round(x, 3) for x in ds.bounds), ds.nodata))
print("all equal grid:", len({r[1:6] for r in allr}) == 1)
