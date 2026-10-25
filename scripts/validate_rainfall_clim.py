import glob, gzip, pathlib
import numpy as np
import rasterio
from rasterio.windows import from_bounds

files = sorted(glob.glob(str(pathlib.Path(r"C:\Major\data\raw\rainfall\chirps_v2_monthly\*.tif.gz"))))
print("files:", len(files))

# integrity of the final month (others verified in the earlier pass)
with gzip.open(files[-1], "rb") as fh:
    while fh.read(1 << 22):
        pass
print("last file ok:", pathlib.Path(files[-1]).name)

years = {}
for f in files:
    y = int(pathlib.Path(f).name.split(".")[2])
    with rasterio.open("/vsigzip/" + f) as ds:
        win = from_bounds(75.60, 11.25, 76.55, 12.00, ds.transform)
        a = ds.read(1, window=win, boundless=True).astype("float64")
        a[a <= -9999] = np.nan
        years.setdefault(y, []).append(np.nanmean(a))

means = {y: sum(v) for y, v in years.items() if len(v) == 12}
print("complete years:", len(means), "| range", min(means), "-", max(means))
for y in sorted(means)[:2] + sorted(means)[-3:]:
    print(f"  {y}: {means[y]:.0f} mm/yr")
print(f"climatology {min(means)}-{max(means)}: {np.mean(list(means.values())):.0f} mm/yr")

monsoon = []
for f in files:
    n = pathlib.Path(f).name
    if n.split(".")[3] in ("06", "07", "08", "09"):
        with rasterio.open("/vsigzip/" + f) as ds:
            win = from_bounds(75.60, 11.25, 76.55, 12.00, ds.transform)
            a = ds.read(1, window=win, boundless=True).astype("float64")
            a[a <= -9999] = np.nan
            monsoon.append(np.nanmean(a))
print(f"mean JJAS monthly rainfall: {np.mean(monsoon):.0f} mm")

