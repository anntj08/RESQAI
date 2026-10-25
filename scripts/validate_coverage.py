import pathlib

import geopandas as gpd
import rasterio
from shapely.geometry import box
from shapely.ops import unary_union

RAW = pathlib.Path(r"C:\Major\data\raw")
g = gpd.read_file(RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
way = g[g["NAME_2"] == "Wayanad"].to_crs(32643)
geom = way.geometry.iloc[0]
district_area = geom.area

def coverage(raster_paths):
    boxes = []
    for p in raster_paths:
        with rasterio.open(p) as ds:
            b = ds.bounds
            boxes.append(box(b.left, b.bottom, b.right, b.top))
    union_wgs = unary_union(boxes)
    union = gpd.GeoSeries([union_wgs], crs=4326).to_crs(32643).iloc[0]
    inside = geom.intersection(union).area
    return 100 * inside / district_area

dem = sorted((RAW / "dem" / "copernicus_glo30").glob("*.tif"))
print(f"Copernicus 2-tile coverage of Wayanad: {coverage(dem):.2f}%")
print(f"Copernicus E076 alone         : {coverage([dem[1]]):.2f}%")
print(f"Copernicus E075 alone         : {coverage([dem[0]]):.2f}%")

srtm = sorted((RAW / "dem" / "srtm_1arcsec_skadi").glob("*.hgt"))
print(f"SRTM 2-tile coverage          : {coverage(srtm):.2f}%")

wc = sorted((RAW / "landcover").glob("*.tif"))
print(f"WorldCover tile coverage      : {coverage(wc):.2f}%")

# how much of district falls west vs east of 76E
from shapely.geometry import LineString
west = geom.intersection(box(75.0, 11.0, 76.0, 12.5)).area / district_area * 100
print(f"district area west of 76E     : {west:.1f}%  -> {100-west:.1f}% east of 76E")
