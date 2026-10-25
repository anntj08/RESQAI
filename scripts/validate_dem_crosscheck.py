import glob
import pathlib

import geopandas as gpd
import numpy as np
import rasterio

RAW = pathlib.Path(r"C:\Major\data\raw")
g = gpd.read_file(RAW / "boundary" / "gadm41_IND_2" / "gadm41_IND_2.json")
way = g[g["NAME_2"] == "Wayanad"]

rng = np.random.default_rng(42)
pts = [(rng.uniform(75.78, 76.43), rng.uniform(11.45, 11.97)) for _ in range(4000)]
pg = gpd.GeoDataFrame(geometry=gpd.points_from_xy([p[0] for p in pts], [p[1] for p in pts]), crs=4326)
pg = pg[pg.within(way.geometry.iloc[0])]
coords = [(p.x, p.y) for p in pg.geometry]
print("sample points inside Wayanad:", len(coords))

def sample_tiled(paths):
    out = np.full(len(coords), np.nan)
    for p in paths:
        with rasterio.open(p) as ds:
            b = ds.bounds
            idx = [i for i, (x, y) in enumerate(coords)
                   if b.left <= x <= b.right and b.bottom <= y <= b.top]
            if not idx:
                continue
            vals = np.array([v[0] for v in ds.sample([coords[i] for i in idx])], dtype="float64")
            nd = ds.nodata
            if nd is not None:
                vals[vals == nd] = np.nan
            vals[vals <= -1000] = np.nan
            out[idx] = vals
    return out

srtm = sample_tiled(sorted(glob.glob(str(RAW / "dem" / "srtm_1arcsec_skadi" / "*.hgt"))))
cop = sample_tiled(sorted(glob.glob(str(RAW / "dem" / "copernicus_glo30" / "*.tif"))))

m = np.isfinite(srtm) & np.isfinite(cop)
d = cop[m] - srtm[m]
print(f"valid pairs: {m.sum()} / {len(coords)}")
print(f"SRTM   mean={srtm[m].mean():.1f} m  range={srtm[m].min():.0f}-{srtm[m].max():.0f}")
print(f"COPDEM mean={cop[m].mean():.1f} m  range={cop[m].min():.0f}-{cop[m].max():.0f}")
print(f"diff (COPDEM-SRTM): mean={d.mean():.2f} m  MAD={np.abs(d).mean():.2f} m  "
      f"median={np.median(d):.2f}  p95|d|={np.percentile(np.abs(d),95):.2f} m  max|d|={np.abs(d).max():.1f} m")
print(f"correlation r={np.corrcoef(srtm[m], cop[m])[0,1]:.4f}")
print(f"points with |diff|>50m: {(np.abs(d)>50).sum()}")
