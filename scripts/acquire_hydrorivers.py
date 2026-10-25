"""HydroRIVERS v1.0 Asia -> Wayanad clip (drainage network for distance-to-river)."""
import pathlib, sys, zipfile
import geopandas as gpd
from shapely.geometry import box

sys.path.insert(0, r"C:\Major\scripts")
from fetch import download

RAW = pathlib.Path(r"C:\Major\data\raw")
PROC = pathlib.Path(r"C:\Major\data\processed")
dest = RAW / "additional" / "hydrorivers"
z = download("https://data.hydrosheds.org/file/HydroRIVERS/HydroRIVERS_v10_as_shp.zip",
             dest / "HydroRIVERS_v10_as_shp.zip", min_bytes=50_000_000)

if not (dest / "HydroRIVERS_v10_as.shp").exists():
    with zipfile.ZipFile(z) as zf:
        zf.extractall(dest)
    print("extracted:", [p.name for p in dest.glob("*.shp")])

shp = next(dest.rglob("HydroRIVERS_v10_as.shp"))
g = gpd.read_file(RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
way = g[g["NAME_2"] == "Wayanad"]
bb = box(75.60, 11.25, 76.55, 12.00)
r = gpd.read_file(shp, bbox=bb)
print("rivers in bbox:", len(r), "crs:", r.crs, "cols:", list(r.columns)[:10])
clip = gpd.clip(r, bb)
print("rivers after clip:", len(clip), "total length km:",
      round(clip.to_crs(32643).length.sum() / 1000, 1))
out = PROC / "additional" / "hydrorivers_wayanad_clip.gpkg"
out.parent.mkdir(parents=True, exist_ok=True)
clip.to_file(out, driver="GPKG")
print("wrote", out, round(out.stat().st_size / 1e6, 2), "MB")
