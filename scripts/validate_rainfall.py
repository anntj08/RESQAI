import glob
import gzip
import pathlib

import numpy as np
import rasterio
from rasterio.windows import from_bounds

RAW = pathlib.Path(r"C:\Major\data\raw")
files = sorted(glob.glob(str(RAW / "rainfall" / "chirps_v2_monthly" / "*.tif.gz")))
print(f"files: {len(files)}")

# 1) gzip stream integrity on every file
bad = []
for f in files:
    try:
        with gzip.open(f, "rb") as fh:
            while fh.read(1 << 22):
                pass
    except Exception:
        bad.append(pathlib.Path(f).name)
print("corrupt gzip files:", bad if bad else "none")

# 2) raster metadata + Wayanad window statistics on a sample
sample = [f for f in files if any(k in f for k in ("2000.06", "2010.06", "2018.06", "2024.07", "2018.08"))]
for f in sample:
    with rasterio.open("/vsigzip/" + f) as ds:
        win = from_bounds(75.60, 11.25, 76.55, 12.00, ds.transform)
        a = ds.read(1, window=win, boundless=True)
        v = a[(a != ds.nodata) & np.isfinite(a)]
        print(f"{pathlib.Path(f).name}: {ds.width}x{ds.height} res={round(ds.res[0],4)} "
              f"crs={ds.crs} nodata={ds.nodata} | Wayanad window: "
              f"min={v.min():.1f} max={v.max():.1f} mean={v.mean():.1f} mm/month")

# 3) multi-year mean annual rainfall over Wayanad window (validation only)
years = {}
for f in files:
    name = pathlib.Path(f).name
    y = int(name.split(".")[1])
    with rasterio.open("/vsigzip/" + f) as ds:
        win = from_bounds(75.60, 11.25, 76.55, 12.00, ds.transform)
        a = ds.read(1, window=win, boundless=True).astype("float64")
        a[a == ds.nodata] = np.nan
        years.setdefault(y, []).append(np.nanmean(a))
means = {y: sum(v) for y, v in years.items() if len(v) == 12}
print("\nmean annual rainfall (mm) over Wayanad window by year:")
for y in sorted(means)[:3] + sorted(means)[-4:]:
    print(f"  {y}: {means[y]:.0f}")
print(f"  climatology {min(means)}-{max(means)}: {np.mean(list(means.values())):.0f} mm/yr")
