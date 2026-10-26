"""Diagnose the rainfall all-NaN-slice warning at p3_rainfall.py:260.

Question to answer with evidence, not assumption:
  1. Which exact warnings are emitted, and from which numpy call?
  2. How many cells in the padded window have no valid year at all?
  3. Do those cells correspond exactly to the documented sea/edge mask?
  4. Is the resulting value NaN (i.e. correct nodata) rather than a fabricated number?

Run: python data/interim/p3/diag_rainfall_warning.py
"""
from __future__ import annotations

import gzip
import pathlib
import warnings

import numpy as np
import rasterio

RAW = pathlib.Path(r"C:\Major\data\raw\rainfall\chirps_v2_monthly")
files = sorted(RAW.glob("chirps-v2.0.*.tif.gz"))
print(f"files: {len(files)}")

# Read only a handful of months is NOT enough to reproduce the annual cube, but the
# all-NaN footprint of a *cell* is a property of the window mask, which is stable
# across months. Read 24 months to characterise it cheaply, then confirm on the
# full annual computation if the footprint is consistent.
NODATA = -9999.0

arrays = []
for p in files[:24]:
    with gzip.open(p, "rb") as f:
        data = f.read()
    with rasterio.io.MemoryFile(data) as mem:
        with mem.open() as ds:
            a = ds.read(1).astype("float64")
            a[a == NODATA] = np.nan
            arrays.append(a)
print("shape:", arrays[0].shape)

cube = np.stack(arrays)
finite_any = np.isfinite(cube).any(axis=0)
print("cells:", cube[0].size)
print("cells with at least one valid month:", int(finite_any.sum()))
print("cells with NO valid month:", int((~finite_any).sum()))

with warnings.catch_warnings(record=True) as caught:
    warnings.simplefilter("always")
    m = np.nanmean(cube, axis=0)
    s = np.nanstd(cube, axis=0, ddof=1)

print("\nwarnings raised:")
for w in caught:
    print(f"  {w.category.__name__}: {w.message}")
print("distinct:", sorted({str(w.message) for w in caught}))

print("\nnanmean cells that are NaN:", int(np.isnan(m).sum()))
print("all-NaN cells that came out NaN:", int((np.isnan(m) & ~finite_any).sum()))
print("NaN mean cells that DID have data (should be 0):", int((np.isnan(m) & finite_any).sum()))
print("no-data cells that did NOT come out NaN (should be 0):", int((~np.isnan(m) & ~finite_any).sum()))

# Do the empty cells form the contiguous western/southern block we expect
# (the Arabian Sea reaches into the 0.5 deg padded window)?
rows, cols = np.nonzero(~finite_any)
if rows.size:
    print(f"\nno-data rows {rows.min()}..{rows.max()} of {m.shape[0]}")
    print(f"no-data cols {cols.min()}..{cols.max()} of {m.shape[1]}")
    print(f"share of window: {rows.size / m.size * 100:.2f}%")
