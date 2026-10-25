import pathlib
import zipfile
import geopandas as gpd
import pandas as pd

RAW = pathlib.Path(r"C:\Major\data\raw")
zpath = RAW / "geology" / "glim" / "LiMW_GIS_2015.gdb.zip"
dest = RAW / "geology" / "glim"
gdb_dir = dest / "LiMW_GIS_2015.gdb"

if not gdb_dir.exists():
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        print("zip entries:", len(names))
        print("top-level:", sorted({n.split('/')[0] for n in names})[:10])
        zf.extractall(dest)
print("extracted:", gdb_dir.exists())

import pyogrio
layers = pyogrio.list_layers(str(gdb_dir))
print("layers:", layers)

g = gpd.read_file(gdb_dir, layer=layers[0][0])
print("features:", len(g), "| crs:", g.crs)
print("columns:", list(g.columns))
for c in g.columns:
    if c != "geometry":
        print(f"  {c}: {g[c].nunique()} unique | sample {g[c].dropna().unique()[:5]}")
print("bounds:", tuple(round(v, 2) for v in g.total_bounds))
