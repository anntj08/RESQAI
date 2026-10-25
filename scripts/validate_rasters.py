import pathlib, glob
import numpy as np
import rasterio

for p in sorted(glob.glob(r"C:\Major\data\raw\dem\**\*.tif", recursive=True) +
                glob.glob(r"C:\Major\data\raw\landcover\**\*.tif", recursive=True)):
    with rasterio.open(p) as ds:
        a = ds.read(1, out_shape=(min(ds.height, 2000), min(ds.width, 2000)))
        print(f"\n{p}")
        print(f"  size={ds.width}x{ds.height} bands={ds.count} dtype={ds.dtypes[0]} crs={ds.crs}")
        print(f"  res={ds.res} bounds={tuple(round(v,4) for v in ds.bounds)} nodata={ds.nodata}")
        print(f"  compress={ds.profile.get('compress')} tiled={ds.profile.get('tiled')}")
        valid = a[a != (ds.nodata if ds.nodata is not None else -9999)]
        if valid.size:
            print(f"  min={valid.min():.2f} max={valid.max():.2f} mean={valid.mean():.2f}")

for p in sorted(glob.glob(r"C:\Major\data\raw\dem\srtm_1arcsec_skadi\*.hgt")):
    with rasterio.open(p) as ds:
        a = ds.read(1)
        print(f"\n{p}")
        print(f"  size={ds.width}x{ds.height} dtype={ds.dtypes[0]} crs={ds.crs} res={ds.res}")
        print(f"  bounds={tuple(round(v,4) for v in ds.bounds)} min={a.min()} max={a.max()}")
        print(f"  voids(-32768)={(a == -32768).sum()}")
