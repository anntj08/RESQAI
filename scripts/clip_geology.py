import pathlib
import geopandas as gpd
import pandas as pd
from shapely.geometry import box

RAW = pathlib.Path(r"C:\Major\data\raw")
PROC = pathlib.Path(r"C:\Major\data\processed")
gdb = RAW / "geology" / "glim" / "LiMW_GIS 2015.gdb"

g = gpd.read_file(RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
way = g[g["NAME_2"] == "Wayanad"].to_crs(4326)
minx, miny, maxx, maxy = way.total_bounds
pad = 0.05
bb = box(minx - pad, miny - pad, maxx + pad, maxy + pad)

bb_native = gpd.GeoSeries([bb], crs=4326).to_crs("ESRI:54012").total_bounds
print("bbox in EckertIV:", tuple(round(v) for v in bb_native))

gl = gpd.read_file(gdb, layer="GLiM_export", bbox=tuple(bb_native))
print("features in bbox:", len(gl), "crs:", gl.crs)
gl_wgs = gl.to_crs(4326)
clip = gpd.clip(gl_wgs, bb)
print("features after clip:", len(clip))

# exact district overlay
inter = gpd.overlay(clip, way[["geometry"]], how="intersection")
print("features intersecting Wayanad:", len(inter))

summary = (inter.assign(area_km2=inter.to_crs(32643).area / 1e6)
           .groupby(["xx", "Litho"])["area_km2"].sum().sort_values(ascending=False).reset_index())
summary["pct_of_district"] = (summary.area_km2 / summary.area_km2.sum() * 100).round(2)
print(summary.head(12).to_string(index=False))

(RAW / "geology" / "glim").mkdir(parents=True, exist_ok=True)
out = PROC / "geology" / "glim_wayanad_clip.gpkg"
out.parent.mkdir(parents=True, exist_ok=True)
clip.to_file(out, driver="GPKG")
summary.to_csv(PROC / "geology" / "glim_wayanad_lithology_summary.csv", index=False)
print("wrote", out, round(out.stat().st_size / 1e6, 2), "MB")
